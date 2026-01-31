"""
State management service for resume functionality.
Handles checkpoint creation, state persistence, and recovery.
"""

import json
import os
import hashlib
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Set
from contextlib import contextmanager

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ScrapingState:
    """Represents the state of a scraping session."""
    
    query: str
    query_hash: str
    max_results: int
    output_file: str
    business_urls: List[str] = field(default_factory=list)
    processed_indices: Set[int] = field(default_factory=set)
    last_processed_index: int = -1
    successful_count: int = 0
    failed_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed: bool = False
    
    def to_dict(self) -> dict:
        """Convert state to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert set to list for JSON serialization
        data['processed_indices'] = list(self.processed_indices)
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ScrapingState':
        """Create state from dictionary."""
        # Convert list back to set
        if 'processed_indices' in data:
            data['processed_indices'] = set(data['processed_indices'])
        return cls(**data)
    
    def mark_processed(self, index: int) -> None:
        """Mark a URL index as processed."""
        self.processed_indices.add(index)
        self.last_processed_index = max(self.last_processed_index, index)
        self.successful_count += 1
        self.updated_at = datetime.now().isoformat()
    
    def mark_failed(self, index: int) -> None:
        """Mark a URL index as failed."""
        self.processed_indices.add(index)
        self.failed_count += 1
        self.updated_at = datetime.now().isoformat()
    
    def get_pending_urls(self) -> List[tuple[int, str]]:
        """Get list of pending URLs with their indices."""
        return [
            (i, url) for i, url in enumerate(self.business_urls)
            if i not in self.processed_indices
        ]
    
    def is_url_processed(self, index: int) -> bool:
        """Check if a URL at given index has been processed."""
        return index in self.processed_indices
    
    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if not self.business_urls:
            return 0.0
        return (len(self.processed_indices) / len(self.business_urls)) * 100


class StateManager:
    """
    Manages scraping state persistence and recovery.
    
    Features:
    - Atomic state updates using temp files
    - Automatic backup creation
    - State validation and recovery
    - Thread-safe operations
    """
    
    STATE_DIR = Path(".scraping_state")
    BACKUP_DIR = STATE_DIR / "backups"
    
    def __init__(self):
        """Initialize state manager."""
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Create state directories if they don't exist."""
        self.STATE_DIR.mkdir(exist_ok=True)
        self.BACKUP_DIR.mkdir(exist_ok=True)
    
    @staticmethod
    def _generate_query_hash(query: str, max_results: int) -> str:
        """Generate a unique hash for query and parameters."""
        content = f"{query.lower().strip()}_{max_results}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _get_state_file_path(self, query_hash: str) -> Path:
        """Get the path to state file for a query hash."""
        return self.STATE_DIR / f"state_{query_hash}.json"
    
    def _create_backup(self, state_file: Path) -> None:
        """Create a backup of the current state file."""
        if not state_file.exists():
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.BACKUP_DIR / f"{state_file.stem}_{timestamp}.json"
        
        try:
            backup_file.write_text(state_file.read_text())
            logger.debug(f"Created backup: {backup_file}")
        except Exception as e:
            logger.warning(f"Failed to create backup: {e}")
    
    def save_state(self, state: ScrapingState) -> None:
        """
        Save scraping state atomically.
        
        Args:
            state: Scraping state to save
        """
        state_file = self._get_state_file_path(state.query_hash)
        temp_file = state_file.with_suffix('.tmp')
        
        try:
            # Create backup of existing state
            if state_file.exists():
                self._create_backup(state_file)
            
            # Write to temporary file first
            with temp_file.open('w', encoding='utf-8') as f:
                json.dump(state.to_dict(), f, indent=2)
            
            # Atomic rename
            temp_file.replace(state_file)
            logger.debug(f"State saved: {state.query} (Progress: {state.progress_percentage:.1f}%)")
            
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            if temp_file.exists():
                temp_file.unlink()
            raise
    
    def load_state(self, query: str, max_results: int) -> Optional[ScrapingState]:
        """
        Load existing state for a query.
        
        Args:
            query: Search query
            max_results: Maximum results
            
        Returns:
            ScrapingState if found and valid, None otherwise
        """
        query_hash = self._generate_query_hash(query, max_results)
        state_file = self._get_state_file_path(query_hash)
        
        if not state_file.exists():
            logger.debug(f"No existing state found for query: {query}")
            return None
        
        try:
            with state_file.open('r', encoding='utf-8') as f:
                data = json.load(f)
            
            state = ScrapingState.from_dict(data)
            
            # Validate state
            if state.completed:
                logger.info(f"Previous scraping session was completed. Starting fresh.")
                return None
            
            logger.info(f"Found existing state: {len(state.processed_indices)}/{len(state.business_urls)} processed")
            return state
            
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return None
    
    def create_new_state(
        self,
        query: str,
        max_results: int,
        output_file: str,
        business_urls: List[str]
    ) -> ScrapingState:
        """
        Create a new scraping state.
        
        Args:
            query: Search query
            max_results: Maximum results
            output_file: Output CSV filename
            business_urls: List of business URLs to scrape
            
        Returns:
            New ScrapingState instance
        """
        query_hash = self._generate_query_hash(query, max_results)
        
        state = ScrapingState(
            query=query,
            query_hash=query_hash,
            max_results=max_results,
            output_file=output_file,
            business_urls=business_urls
        )
        
        self.save_state(state)
        logger.info(f"Created new scraping state: {len(business_urls)} URLs to process")
        
        return state
    
    def update_state(self, state: ScrapingState, save_interval: int = 5) -> None:
        """
        Update state with auto-save throttling.
        
        Args:
            state: State to update
            save_interval: Save every N updates (default: 5)
        """
        # Save periodically to reduce I/O
        if state.successful_count % save_interval == 0:
            self.save_state(state)
    
    def mark_completed(self, state: ScrapingState) -> None:
        """
        Mark scraping session as completed.
        
        Args:
            state: State to mark as completed
        """
        state.completed = True
        state.updated_at = datetime.now().isoformat()
        self.save_state(state)
        logger.info(f"Scraping session marked as completed")
    
    def delete_state(self, query: str, max_results: int) -> None:
        """
        Delete state file for a query.
        
        Args:
            query: Search query
            max_results: Maximum results
        """
        query_hash = self._generate_query_hash(query, max_results)
        state_file = self._get_state_file_path(query_hash)
        
        if state_file.exists():
            self._create_backup(state_file)
            state_file.unlink()
            logger.info(f"Deleted state file: {state_file}")
    
    def list_active_states(self) -> List[ScrapingState]:
        """
        List all active (incomplete) scraping states.
        
        Returns:
            List of active scraping states
        """
        active_states = []
        
        for state_file in self.STATE_DIR.glob("state_*.json"):
            try:
                with state_file.open('r', encoding='utf-8') as f:
                    data = json.load(f)
                
                state = ScrapingState.from_dict(data)
                if not state.completed:
                    active_states.append(state)
                    
            except Exception as e:
                logger.warning(f"Failed to load state from {state_file}: {e}")
        
        return active_states
    
    @contextmanager
    def managed_state(
        self,
        query: str,
        max_results: int,
        output_file: str,
        business_urls: Optional[List[str]] = None
    ):
        """
        Context manager for state lifecycle.
        
        Usage:
            with state_manager.managed_state(query, max_results, output_file, urls) as state:
                # Process URLs
                state.mark_processed(index)
        
        Args:
            query: Search query
            max_results: Maximum results
            output_file: Output filename
            business_urls: List of URLs (for new state)
            
        Yields:
            ScrapingState instance
        """
        # Try to load existing state
        state = self.load_state(query, max_results)
        
        # Create new state if none exists
        if state is None:
            if business_urls is None:
                raise ValueError("business_urls required for new state")
            state = self.create_new_state(query, max_results, output_file, business_urls)
        
        try:
            yield state
        finally:
            # Final save on exit
            self.save_state(state)


# Singleton instance
_state_manager: Optional[StateManager] = None


def get_state_manager() -> StateManager:
    """Get or create the global state manager instance."""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager
