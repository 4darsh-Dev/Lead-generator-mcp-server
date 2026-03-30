"""State management for Startup India scraper resume support."""

import hashlib
import json
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class StartupIndiaState:
    """Persistent state of a Startup India scraping run."""

    search_url: str
    search_hash: str
    output_file: str
    run_id: str
    discovered_profile_urls: List[str] = field(default_factory=list)
    listing_details: Dict[str, Dict[str, str]] = field(default_factory=dict)
    processed_profile_urls: Set[str] = field(default_factory=set)
    duplicate_profile_urls: Set[str] = field(default_factory=set)
    failed_attempts: Dict[str, int] = field(default_factory=dict)
    completed_listing_discovery: bool = False
    successful_count: int = 0
    duplicate_count: int = 0
    failed_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed: bool = False

    def to_dict(self) -> dict:
        data = asdict(self)
        data["processed_profile_urls"] = list(self.processed_profile_urls)
        data["duplicate_profile_urls"] = list(self.duplicate_profile_urls)
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "StartupIndiaState":
        data["processed_profile_urls"] = set(data.get("processed_profile_urls", []))
        data["duplicate_profile_urls"] = set(data.get("duplicate_profile_urls", []))
        return cls(**data)

    def pending_profile_urls(self, max_retries: int) -> List[str]:
        pending = []
        for profile_url in self.discovered_profile_urls:
            if profile_url in self.processed_profile_urls:
                continue
            if profile_url in self.duplicate_profile_urls:
                continue
            attempts = self.failed_attempts.get(profile_url, 0)
            if attempts >= max_retries:
                continue
            pending.append(profile_url)
        return pending


class StartupIndiaStateManager:
    """Manages state files for Startup India scraping sessions."""

    STATE_DIR = Path(".scraping_state") / "startup_india"
    BACKUP_DIR = STATE_DIR / "backups"

    def __init__(self):
        self.STATE_DIR.mkdir(parents=True, exist_ok=True)
        self.BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _generate_hash(search_url: str) -> str:
        raw = search_url.strip().lower()
        return hashlib.md5(raw.encode()).hexdigest()[:12]

    def _state_file(self, search_hash: str) -> Path:
        return self.STATE_DIR / f"state_{search_hash}.json"

    def save_state(self, state: StartupIndiaState) -> None:
        state.updated_at = datetime.utcnow().isoformat()
        state_path = self._state_file(state.search_hash)
        tmp_path = state_path.with_suffix(".tmp")

        if state_path.exists():
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_path = self.BACKUP_DIR / f"{state_path.stem}_{timestamp}.json"
            try:
                backup_path.write_text(state_path.read_text(encoding="utf-8"), encoding="utf-8")
            except Exception as exc:
                logger.warning("Failed to create state backup: %s", exc)

        try:
            tmp_path.write_text(json.dumps(state.to_dict(), indent=2), encoding="utf-8")
            tmp_path.replace(state_path)
        except Exception:
            if tmp_path.exists():
                tmp_path.unlink()
            raise

    def load_state(self, search_url: str) -> Optional[StartupIndiaState]:
        search_hash = self._generate_hash(search_url)
        state_path = self._state_file(search_hash)
        if not state_path.exists():
            return None

        try:
            payload = json.loads(state_path.read_text(encoding="utf-8"))
            state = StartupIndiaState.from_dict(payload)
            if state.completed:
                return None
            return state
        except Exception as exc:
            logger.error("Failed to load state file %s: %s", state_path, exc)
            return None

    def create_state(self, search_url: str, output_file: str) -> StartupIndiaState:
        search_hash = self._generate_hash(search_url)
        run_id = datetime.utcnow().strftime("startup_india_%Y%m%d_%H%M%S")
        state = StartupIndiaState(
            search_url=search_url,
            search_hash=search_hash,
            output_file=output_file,
            run_id=run_id,
        )
        self.save_state(state)
        return state

    def mark_completed(self, state: StartupIndiaState) -> None:
        state.completed = True
        self.save_state(state)

    @contextmanager
    def managed_state(self, search_url: str, output_file: str, resume: bool):
        state = self.load_state(search_url) if resume else None
        if state is None:
            state = self.create_state(search_url=search_url, output_file=output_file)
        try:
            yield state
        finally:
            self.save_state(state)
