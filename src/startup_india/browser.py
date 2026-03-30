"""Async Playwright browser helpers for Startup India scraping."""

import asyncio
from pathlib import Path
import random
from typing import Dict, List
from urllib.parse import urljoin

from playwright.async_api import async_playwright, Browser, BrowserContext, Frame, Page, Playwright

from src.startup_india.constants import (
    BASE_DOMAIN,
    DISCOVERY_IDLE_ROUNDS,
    LISTING_PAGE_TIMEOUT_MS,
    LOAD_MORE_SELECTOR,
    NO_MORE_SELECTOR,
    RESULT_LINK_SELECTOR,
    RESULT_TILE_SELECTOR,
)
from src.startup_india.models import StartupListingItem
from src.utils.logger import get_logger

logger = get_logger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
]


class StartupIndiaBrowser:
    """Encapsulates async browser lifecycle and listing discovery."""

    def __init__(self, headless: bool = True, slow_mo: int = 0):
        self.headless = headless
        self.slow_mo = slow_mo
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None

    async def start(self) -> None:
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless, slow_mo=self.slow_mo)
        self.context = await self.browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            locale="en-US",
            timezone_id="Asia/Kolkata",
            viewport={"width": 1366, "height": 768},
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Upgrade-Insecure-Requests": "1",
                "DNT": "1",
            },
        )

    async def close(self) -> None:
        if self.context:
            await self.context.close()
            self.context = None
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

    async def new_page(self) -> Page:
        if self.context is None:
            raise RuntimeError("Browser context is not initialized")
        page = await self.context.new_page()
        return page

    async def discover_listing_items(
        self,
        search_url: str,
        existing_details: Dict[str, Dict[str, str]],
        max_profiles: int = 0,
    ) -> Dict[str, Dict[str, str]]:
        """Load all listing cards via load-more and return profile-url keyed details."""
        page = await self.new_page()
        try:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=LISTING_PAGE_TIMEOUT_MS)
            html = await page.content()
            if "403 ERROR" in html and "cloudfront" in html.lower():
                raise PermissionError("CloudFront blocked this scraping session (HTTP 403)")
            search_context = await self._resolve_search_context(page)

            idle_rounds = 0
            last_count = 0

            while True:
                current_items = await self._parse_listing_cards(search_context, listing_url=page.url)
                for item in current_items:
                    existing_details[item.profile_url] = {
                        "name": item.name,
                        "stage": item.stage,
                        "city": item.city,
                        "state": item.state,
                        "industry": item.industry,
                        "profile_url": item.profile_url,
                        "listing_url": item.listing_url,
                    }

                if max_profiles and len(existing_details) >= max_profiles:
                    logger.info("Discovery reached max_profiles=%d", max_profiles)
                    break

                current_count = len(existing_details)
                if current_count == last_count:
                    idle_rounds += 1
                else:
                    idle_rounds = 0
                last_count = current_count

                if idle_rounds >= DISCOVERY_IDLE_ROUNDS:
                    logger.info("No new listings after %d rounds; stopping discovery", DISCOVERY_IDLE_ROUNDS)
                    break

                load_more = await search_context.query_selector(LOAD_MORE_SELECTOR)
                if not load_more:
                    if await search_context.query_selector(NO_MORE_SELECTOR):
                        logger.info("No more results indicator found")
                    break

                try:
                    await load_more.scroll_into_view_if_needed(timeout=10000)
                    await load_more.click(timeout=10000)
                except Exception:
                    try:
                        await page.evaluate(
                            """
                            () => {
                                const el = document.querySelector('#loadmoreicon');
                                if (el) { el.click(); }
                            }
                            """
                        )
                    except Exception:
                        break

                await page.wait_for_load_state("networkidle", timeout=10000)
                await asyncio.sleep(1.5)

            return existing_details
        finally:
            await page.close()

    async def _resolve_search_context(self, page: Page) -> Page | Frame:
        """Resolve whether results are in main page or an embedded frame."""
        for _ in range(45):
            page_count = await page.locator(RESULT_TILE_SELECTOR).count()
            if page_count > 0:
                return page

            for frame in page.frames:
                try:
                    count = await frame.locator(RESULT_TILE_SELECTOR).count()
                    if count > 0:
                        return frame
                except Exception:
                    continue

            await asyncio.sleep(1.5)

        debug_dir = Path(".scraping_state") / "startup_india"
        debug_dir.mkdir(parents=True, exist_ok=True)
        debug_file = debug_dir / "debug_last_search.html"
        debug_file.write_text(await page.content(), encoding="utf-8")
        raise TimeoutError(
            f"Startup India result tiles not found after waiting. Debug saved at {debug_file}"
        )

    async def _parse_listing_cards(self, search_context: Page | Frame, listing_url: str) -> List[StartupListingItem]:
        cards = await search_context.query_selector_all(RESULT_TILE_SELECTOR)
        items: List[StartupListingItem] = []

        for card in cards:
            link = await card.query_selector(RESULT_LINK_SELECTOR)
            if not link:
                continue

            href = (await link.get_attribute("href")) or ""
            if not href:
                continue
            profile_url = href if href.startswith("http") else urljoin(BASE_DOMAIN, href)

            name_node = await card.query_selector(".events-details h3")
            stage_node = await card.query_selector(".events-details .highlighted-text")
            city_node = await card.query_selector(".events-details li.location span:nth-child(1)")
            state_node = await card.query_selector(".events-details li.location span:nth-child(2)")
            industry_node = await card.query_selector(".down-dept .dept")

            name = ((await name_node.inner_text()) if name_node else "").strip()
            stage = ((await stage_node.inner_text()) if stage_node else "").strip()
            city = ((await city_node.inner_text()) if city_node else "").strip().rstrip(",")
            state = ((await state_node.inner_text()) if state_node else "").strip()
            industry = ((await industry_node.inner_text()) if industry_node else "").strip()

            items.append(
                StartupListingItem(
                    name=name,
                    stage=stage,
                    city=city,
                    state=state,
                    industry=industry,
                    profile_url=profile_url,
                    listing_url=listing_url,
                )
            )

        return items
