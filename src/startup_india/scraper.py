"""Async scraper for Startup India startup profiles with resume support."""

import asyncio
from datetime import datetime
import re
from typing import Dict, Optional
from tqdm import tqdm

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
                if not output_file:
                    output_file = state.output_file

            resolved_output = self._resolve_output_filename(output_file, state)
            state.output_file = resolved_output

            if (
                not state.completed_listing_discovery
                and not state.discovered_profile_urls
                and state.listing_details
            ):
                recovered_urls = list(state.listing_details.keys())
                state.discovered_profile_urls = recovered_urls
                state.completed_listing_discovery = True
                self.state_manager.save_state(state)
                logger.info(
                    "Recovered %d discovered profile urls from saved state; proceeding to extraction",
                    len(recovered_urls),
                )

            self.csv_store.open(filename=resolved_output, resume=resuming)

            live_extraction_tasks: list[asyncio.Task] = []
            live_extraction_enabled = False

            if not state.completed_listing_discovery:
                logger.info("Starting listing discovery")
                live_extraction_enabled = True
                live_semaphore = asyncio.Semaphore(self.concurrency)
                scheduled_profile_urls: set[str] = set()
                processed_since_checkpoint = 0

                extraction_total = max_profiles if max_profiles > 0 else None
                extraction_bar = tqdm(
                    total=extraction_total,
                    desc="Extracting profiles",
                    unit="profile",
                    dynamic_ncols=True,
                )

                def on_extraction_task_done(task: asyncio.Task) -> None:
                    nonlocal processed_since_checkpoint
                    extraction_bar.update(1)
                    processed_since_checkpoint += 1
                    if processed_since_checkpoint >= self.checkpoint_interval:
                        processed_since_checkpoint = 0
                        self.state_manager.save_state(state)

                    if task.cancelled():
                        return
                    exc = task.exception()
                    if exc:
                        logger.debug("Live extraction task failed: %s", exc)

                async def on_new_listing_items(items) -> None:
                    for item in items:
                        profile_url = item.profile_url
                        if profile_url in scheduled_profile_urls:
                            continue

                        if profile_url not in state.discovered_profile_urls:
                            state.discovered_profile_urls.append(profile_url)

                        scheduled_profile_urls.add(profile_url)
                        task = asyncio.create_task(
                            self._process_profile_url(
                                profile_url=profile_url,
                                state=state,
                                semaphore=live_semaphore,
                            )
                        )
                        task.add_done_callback(on_extraction_task_done)
                        live_extraction_tasks.append(task)

                discovery_total = max_profiles if max_profiles > 0 else None
                discovery_bar = tqdm(
                    total=discovery_total,
                    desc="Discovering listings",
                    unit="profile",
                    dynamic_ncols=True,
                )

                last_discovery_count = 0

                def on_discovery_progress(current_count: int) -> None:
                    nonlocal last_discovery_count
                    delta = max(0, current_count - last_discovery_count)
                    if delta:
                        discovery_bar.update(delta)
                    last_discovery_count = current_count

                try:
                    listing_details = await self.browser.discover_listing_items(
                        search_url=normalized_url,
                        existing_details=state.listing_details,
                        max_profiles=max_profiles,
                        on_discovery_progress=on_discovery_progress,
                        on_new_listing_items=on_new_listing_items,
                    )
                finally:
                    discovery_bar.close()

                state.listing_details = listing_details
                state.discovered_profile_urls = list(listing_details.keys())
                state.completed_listing_discovery = True
                self.state_manager.save_state(state)
                logger.info("Discovery complete: %d profile urls", len(state.discovered_profile_urls))

                try:
                    if live_extraction_tasks:
                        await asyncio.gather(*live_extraction_tasks, return_exceptions=True)
                finally:
                    extraction_bar.close()
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

            if live_extraction_enabled:
                logger.info("Pending profiles after live extraction: %d", len(pending_urls))

            semaphore = asyncio.Semaphore(self.concurrency)

            tasks = [
                asyncio.create_task(self._process_profile_url(url, state, semaphore))
                for url in pending_urls
            ]

            processed_since_checkpoint = 0
            extraction_bar = tqdm(
                total=len(pending_urls),
                desc="Extracting profiles",
                unit="profile",
                dynamic_ncols=True,
            )

            try:
                for task in asyncio.as_completed(tasks):
                    await task
                    extraction_bar.update(1)
                    processed_since_checkpoint += 1
                    if processed_since_checkpoint >= self.checkpoint_interval:
                        processed_since_checkpoint = 0
                        self.state_manager.save_state(state)
            finally:
                extraction_bar.close()

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
        logger.warning(
            "Profile failed after %d attempts: %s",
            self.max_retries,
            profile_url,
        )

    async def _extract_profile(self, profile_url: str, state: StartupIndiaState) -> Dict[str, str]:
        listing_data = state.listing_details.get(profile_url, {})
        page = await self.browser.new_page()

        try:
            await page.goto(profile_url, wait_until="domcontentloaded", timeout=PROFILE_PAGE_TIMEOUT_MS)
            await self._wait_for_profile_render(page)

            name = await self._read_text(page, PROFILE_NAME_SELECTOR, listing_data.get("name", ""))
            phone = await self._read_first_text(
                page,
                selectors=[
                    PROFILE_PHONE_SELECTOR,
                    ".user-profile-banner .company-name .telephone",
                    ".company-name span.telephone",
                    "span.telephone",
                ],
                default="",
            )
            phone = self._clean_whitespace(phone)

            email = await self._read_first_text(
                page,
                selectors=[
                    PROFILE_EMAIL_SELECTOR,
                    ".user-profile-banner .company-name .mail",
                    ".company-name span.mail",
                    "span.mail",
                ],
                default="",
            )
            email = self._clean_whitespace(email)

            website = await self._read_first_attribute(
                page,
                selectors=[
                    PROFILE_WEBSITE_SELECTOR,
                    ".user-profile-banner .company-name a.website",
                    ".company-name a.website[href^='http']",
                    "a.website[href^='http']",
                    ".company-name a[href^='http']",
                ],
                attribute="href",
                default="",
            )
            website = self._clean_whitespace(website)

            page_text = ""
            if not phone or not email or not website:
                try:
                    page_text = await page.locator("body").inner_text()
                except Exception:
                    page_text = ""

            if not phone and page_text:
                phone_match = re.search(r"\b(?:\+91[-\s]?)?[0-9]{10}\b", page_text)
                if phone_match:
                    phone = phone_match.group(0)

            if not email and page_text:
                email_match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", page_text)
                if email_match:
                    email = email_match.group(0)

            if not website and page_text:
                website_match = re.search(r"https?://[^\s\"'<>]+", page_text)
                if website_match:
                    website = website_match.group(0).rstrip(".,)")

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
    async def _wait_for_profile_render(page) -> None:
        selectors = [
            PROFILE_NAME_SELECTOR,
            ".user-profile-banner .company-name",
            ".company-name .telephone, .company-name .mail, .company-name a.website",
        ]
        for selector in selectors:
            try:
                await page.wait_for_selector(selector, timeout=12000)
                break
            except Exception:
                continue

        await asyncio.sleep(1.0)

    @staticmethod
    def _clean_whitespace(value: str) -> str:
        return re.sub(r"\s+", " ", (value or "")).strip()

    @staticmethod
    async def _read_first_text(page, selectors: list[str], default: str) -> str:
        for selector in selectors:
            value = await StartupIndiaScraper._read_text(page, selector, "")
            value = StartupIndiaScraper._clean_whitespace(value)
            if value:
                return value
        return default

    @staticmethod
    async def _read_first_attribute(page, selectors: list[str], attribute: str, default: str) -> str:
        for selector in selectors:
            value = await StartupIndiaScraper._read_attribute(page, selector, attribute, "")
            value = StartupIndiaScraper._clean_whitespace(value)
            if value:
                return value
        return default

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
