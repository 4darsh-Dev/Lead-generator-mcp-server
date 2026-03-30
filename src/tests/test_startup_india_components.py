"""Unit tests for Startup India scraper components."""

from src.startup_india.constants import enforce_startup_scaling_filters
from src.startup_india.persistence import StartupIndiaCsvStore
from src.startup_india.state import StartupIndiaState


def test_enforce_startup_scaling_filters_overwrites_params():
    url = "https://www.startupindia.gov.in/content/sih/en/search.html?roles=Mentor&stages=idea&page=4"
    normalized = enforce_startup_scaling_filters(url)

    assert "roles=Startup" in normalized
    assert "stages=scaling" in normalized
    assert "roles=Mentor" not in normalized
    assert "stages=idea" not in normalized


def test_composite_dedupe_key_normalizes_values():
    row1 = {
        "name": "  Daksyam Technologies LLP ",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "website": "http://www.daksyam.com/",
    }
    row2 = {
        "name": "daksyam technologies llp",
        "city": "chennai",
        "state": "tamil nadu",
        "website": "http://www.daksyam.com",
    }

    assert StartupIndiaCsvStore.build_dedupe_key(row1) == StartupIndiaCsvStore.build_dedupe_key(row2)


def test_state_pending_urls_respects_processed_duplicates_and_retries():
    state = StartupIndiaState(
        search_url="https://www.startupindia.gov.in/content/sih/en/search.html?roles=Startup&stages=scaling&page=1",
        search_hash="abc123",
        output_file="out.csv",
        run_id="run_1",
        discovered_profile_urls=["u1", "u2", "u3", "u4"],
        processed_profile_urls={"u1"},
        duplicate_profile_urls={"u2"},
        failed_attempts={"u3": 3, "u4": 1},
    )

    pending = state.pending_profile_urls(max_retries=3)
    assert pending == ["u4"]
