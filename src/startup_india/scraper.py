"""Async scraper for Startup India startup profiles with resume support."""

import asyncio
from datetime import datetime
from typing import Dict, Optional

from src.startup_india.browser import StartupIndiaBrowser
from src.startup_india.constants import (
    DEFAULT_CHECKPOINT_INTERVAL,
    DEFAULT_CONCURRENCY,
    DEFAULT_MAX_RETRIES,
    PROFILE_ACTIVE_SINCE_SELECTOR,
    PROFILE_DESCRIPTION_SELECTOR,
    PROFILE_EMAIL_SELECTOR,
    PROFILE_ENGAGEMENT_SELECTOR,
    PROFILE_NAME_SELECTOR,
    PROFILE_PAGE_TIMEOUT_MS,
    PROFILE_PHONE_SELECTOR,
    PROFILE_WEBSITE_SELECTOR,
    enforce_startup_scaling_filters,
)
from src.startup_india.models import StartupProfileData
from src.startup_india.persistence import StartupIndiaCsvStore
from src.startup_india.state import StartupIndiaState, StartupIndiaStateManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class StartupIndiaScraper:
    """Orchestrates async scrape flow for Startup India profiles."""

    def __init__(
        self,
        headless: bool = True,
        slow_mo: int = 0,
        concurrency: int = DEFAULT_CONCURRENCY,
        checkpoint_interval: int = DEFAULT_CHECKPOINT_INTERVAL,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ):
        self.headless = headless
        self.slow_mo = slow_mo
        self.concurrency = max(1, concurrency)
        self.checkpoint_interval = max(1, checkpoint_interval)
        self.max_retries = max(1, max_retries)

        self.browser = StartupIndiaBrowser(headless=headless, slow_mo=slow_mo)
        self.state_manager = StartupIndiaStateManager()
        self.csv_store = StartupIndiaCsvStore()

    async def run(
        self,
        search_url: str,
        output_file: Optional[str],
        resume: bool = True,
        max_profiles: int = 0,
    ) -> Optional[str]:
        """Run full listing discovery + profile extraction + incremental save pipeline."""
        normalized_url = enforce_startup_scaling_filters(search_url)

        try:
            await self.browser.start()

            state = self.state_manager.load_state(normalized_url) if resume else None
            resuming = state is not None

            if not resuming:
                state = self.state_manager.create_state(normalized_url, output_file or "")
            else:
                logger.info(
                    "Resuming Startup India run: %d processed, %d discovered",
                    len(state.processed_profile_urls),
                    len(state.discovered_profile_urls),
                )
                output_file = state.output_file

            resolved_output = self._resolve_output_filename(output_file, state)
            state.output_file = resolved_output

            self.csv_store.open(filename=resolved_output, resume=resuming)

            if not state.completed_listing_discovery:
                logger.info("Starting listing discovery")
                listing_details = await self.browser.discover_listing_items(
                    search_url=normalized_url,
                    existing_details=state.listing_details,
                    max_profiles=max_profiles,
                )
                state.listing_details = listing_details
                state.discovered_profile_urls = list(listing_details.keys())
                state.completed_listing_discovery = True
                self.state_manager.save_state(state)
                logger.info("Discovery complete: %d profile urls", len(state.discovered_profile_urls))
            else:
                logger.info(
                    "Using discovered URLs from state: %d",
                    len(state.discovered_profile_urls),
                )

            pending_urls = state.pending_profile_urls(max_retries=self.max_retries)
            if max_profiles:
                pending_urls = pending_urls[:max_profiles]

            logger.info("Pending profiles for extraction: %d", len(pending_urls))
            if not pending_urls:
                self.state_manager.mark_completed(state)
                return resolved_output

            semaphore = asyncio.Semaphore(self.concurrency)

            tasks = [
                asyncio.create_task(self._process_profile_url(url, state, semaphore))
                for url in pending_urls
            ]

            processed_since_checkpoint = 0
            for task in asyncio.as_completed(tasks):
                await task
                processed_since_checkpoint += 1
                if processed_since_checkpoint >= self.checkpoint_interval:
                    processed_since_checkpoint = 0
                    self.state_manager.save_state(state)

            self.state_manager.mark_completed(state)
            logger.info(
                "Startup India scrape completed: success=%d duplicate=%d failed=%d",
                state.successful_count,
                state.duplicate_count,
                state.failed_count,
            )
            return resolved_output

        except KeyboardInterrupt:
            logger.warning("Startup India scrape interrupted by user")
            if state:
                self.state_manager.save_state(state)
            raise
        except PermissionError as exc:
            logger.error("Startup India access blocked: %s", exc)
            logger.error("Try running with --visible, slower pace, or from a different network/IP.")
            if state:
                self.state_manager.save_state(state)
            return None
        except Exception as exc:
            logger.error("Startup India scrape failed: %s", exc, exc_info=True)
            if state:
                self.state_manager.save_state(state)
            return None
        finally:
            self.csv_store.close()
            await self.browser.close()

    async def _process_profile_url(
        self,
        profile_url: str,
        state: StartupIndiaState,
        semaphore: asyncio.Semaphore,
    ) -> None:
        attempts = state.failed_attempts.get(profile_url, 0)
        while attempts < self.max_retries:
            attempts += 1
            try:
                async with semaphore:
                    row = await self._extract_profile(profile_url=profile_url, state=state)

                was_new = await self.csv_store.append_if_new(row)
                if was_new:
                    state.successful_count += 1
                    state.processed_profile_urls.add(profile_url)
                    return

                state.duplicate_count += 1
                state.duplicate_profile_urls.add(profile_url)
                return
            except Exception as exc:
                state.failed_attempts[profile_url] = attempts
                logger.debug(
                    "Profile extraction failed (%s) attempt %d/%d: %s",
                    profile_url,
                    attempts,
                    self.max_retries,
                    exc,
                )
                await asyncio.sleep(min(1.5 * attempts, 5))

        state.failed_count += 1

    async def _extract_profile(self, profile_url: str, state: StartupIndiaState) -> Dict[str, str]:
        listing_data = state.listing_details.get(profile_url, {})
        page = await self.browser.new_page()

        try:
            await page.goto(profile_url, wait_until="domcontentloaded", timeout=PROFILE_PAGE_TIMEOUT_MS)

            name = await self._read_text(page, PROFILE_NAME_SELECTOR, listing_data.get("name", ""))
            phone = await self._read_text(page, PROFILE_PHONE_SELECTOR, "")
            phone = phone.replace("\n", " ").replace("\t", " ").strip()

            email = await self._read_text(page, PROFILE_EMAIL_SELECTOR, "")
            email = email.replace("\n", " ").replace("\t", " ").strip()

            website = await self._read_attribute(page, PROFILE_WEBSITE_SELECTOR, "href", "")
            description = await self._read_text(page, PROFILE_DESCRIPTION_SELECTOR, "")
            engagement_level = await self._read_text(page, PROFILE_ENGAGEMENT_SELECTOR, "")
            active_since = await self._read_text(page, PROFILE_ACTIVE_SINCE_SELECTOR, "")

            model = StartupProfileData(
                name=name,
                stage=listing_data.get("stage", ""),
                city=listing_data.get("city", ""),
                state=listing_data.get("state", ""),
                industry=listing_data.get("industry", ""),
                phone=phone,
                email=email,
                website=website,
                description=description,
                engagement_level=engagement_level,
                active_since=active_since,
                profile_url=profile_url,
                listing_url=listing_data.get("listing_url", state.search_url),
                run_id=state.run_id,
                scraped_at=datetime.utcnow().isoformat(),
            )
            return model.to_row()
        finally:
            await page.close()

    @staticmethod
    async def _read_text(page, selector: str, default: str) -> str:
        node = await page.query_selector(selector)
        if not node:
            return default
        value = await node.inner_text()
        value = (value or "").strip()
        return value if value else default

    @staticmethod
    async def _read_attribute(page, selector: str, attribute: str, default: str) -> str:
        node = await page.query_selector(selector)
        if not node:
            return default
        value = await node.get_attribute(attribute)
        value = (value or "").strip()
        return value if value else default

    @staticmethod
    def _resolve_output_filename(output_file: str, state: StartupIndiaState) -> str:
        if output_file:
            return output_file
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"startup_india_scaling_{timestamp}.csv"
