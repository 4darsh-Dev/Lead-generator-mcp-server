"""Incremental CSV persistence with deduplication for Startup India scraper."""

import asyncio
import csv
import os
from pathlib import Path
from typing import Dict, List, Optional, Set

from src.utils.logger import get_logger

logger = get_logger(__name__)


class StartupIndiaCsvStore:
    """Append-mode CSV writer with composite-key dedupe."""

    FIELDNAMES: List[str] = [
        "name",
        "stage",
        "city",
        "state",
        "industry",
        "phone",
        "email",
        "website",
        "description",
        "engagement_level",
        "active_since",
        "profile_url",
        "listing_url",
        "run_id",
        "scraped_at",
    ]

    def __init__(self):
        self.file_handle = None
        self.writer = None
        self.filename: Optional[str] = None
        self.lock = asyncio.Lock()
        self.known_keys: Set[str] = set()

    @staticmethod
    def build_dedupe_key(row: Dict[str, str]) -> str:
        name = (row.get("name") or "").strip().casefold()
        city = (row.get("city") or "").strip().casefold()
        state = (row.get("state") or "").strip().casefold()
        website = (row.get("website") or "").strip().rstrip("/").casefold()
        return "|".join([name, city, state, website])

    def open(self, filename: str, resume: bool) -> str:
        self.filename = filename
        path = Path(filename)
        file_exists = path.exists()

        mode = "a" if resume and file_exists else "w"
        self.file_handle = open(filename, mode, newline="", encoding="utf-8")
        self.writer = csv.DictWriter(self.file_handle, fieldnames=self.FIELDNAMES, extrasaction="ignore")

        if mode == "w":
            self.writer.writeheader()
            self.file_handle.flush()
            os.fsync(self.file_handle.fileno())

        if resume and file_exists:
            self._load_existing_keys(path)

        logger.info("CSV store ready: %s (resume=%s)", filename, resume and file_exists)
        return filename

    def _load_existing_keys(self, path: Path) -> None:
        try:
            with path.open("r", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                for row in reader:
                    self.known_keys.add(self.build_dedupe_key(row))
            logger.info("Loaded %d existing dedupe keys", len(self.known_keys))
        except Exception as exc:
            logger.warning("Failed loading existing keys from %s: %s", path, exc)

    async def append_if_new(self, row: Dict[str, str]) -> bool:
        key = self.build_dedupe_key(row)
        async with self.lock:
            if key in self.known_keys:
                return False
            self.writer.writerow(row)
            self.file_handle.flush()
            os.fsync(self.file_handle.fileno())
            self.known_keys.add(key)
            return True

    def close(self) -> None:
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None
            self.writer = None
