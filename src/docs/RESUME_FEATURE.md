# Resume & State Management Feature

## Overview

The Lead Generator now includes automatic **resume functionality** and **improved scrolling** to handle larger datasets efficiently. This means:

1. ✅ **Better Loading**: Improved scrolling can load more results (beyond the 120 limit)
2. ✅ **Auto-Resume**: If scraping stops, you can resume from where it left off
3. ✅ **No Duplicates**: Resuming won't create duplicate entries
4. ✅ **Progress Tracking**: View progress of ongoing and paused sessions

## Key Features

### 1. Improved Result Loading

**What was the problem?**
- Scraping would stop at ~120 results even when requesting 1000
- Google Maps wouldn't load more results with basic scrolling

**How it's fixed:**
- More aggressive scrolling strategy with multiple scroll actions
- Increased scroll attempts from 20 to 50
- Better timing and detection of when all available results are loaded
- Longer pause times (2s + random delay) to allow content to load

### 2. Automatic Resume Functionality

**What was the problem?**
- If scraping stopped (error, network issue, Ctrl+C), you'd have to start from scratch
- All progress would be lost

**How it works:**
- Creates a `.scraping_state/` directory with session state files
- Tracks:
  - All collected business URLs
  - Which URLs have been processed
  - Output filename
  - Progress statistics
- When you run the same command again, it automatically resumes
- Appends new data to existing CSV file
- Skips already-processed businesses

### 3. Duplicate Prevention

- Loads existing business names from CSV on resume
- Skips businesses already scraped
- Case-insensitive name matching

## Usage

### Basic Scraping (with auto-resume enabled)

```bash
python main.py --query "Interior Designers in New Delhi" --max-results 1000 --output delhi_interior.csv
```

If this stops at 120 results or gets interrupted:
- Progress is automatically saved
- Just run the **exact same command** again to resume

### Disable Resume (start fresh)

```bash
python main.py --query "Interior Designers in New Delhi" --max-results 1000 --output new_file.csv --no-resume
```

### View Active Sessions

```bash
python main.py --show-sessions
```

Example output:
```
📊 Active Scraping Sessions (2):
================================================================================

1. Query: Interior Designers in New Delhi
   Max Results: 1000
   Output File: delhi_interior.csv
   Progress: 120/350 (34.3%)
   Successful: 108 | Failed: 12
   Last Updated: 2026-01-31T10:30:45

2. Query: Coffee Shops in Mumbai
   Max Results: 500
   Output File: mumbai_coffee.csv
   Progress: 200/450 (44.4%)
   Successful: 195 | Failed: 5
   Last Updated: 2026-01-31T09:15:22

================================================================================

💡 Tip: Run the same command to resume any session.
```

## State Management

### State Directory Structure

```
.scraping_state/
├── state_<hash1>.json          # Active session 1
├── state_<hash2>.json          # Active session 2
└── backups/
    ├── state_<hash1>_20260131_103045.json
    └── state_<hash2>_20260131_091522.json
```

### State File Contents

Each state file contains:
```json
{
  "query": "Interior Designers in New Delhi",
  "query_hash": "a1b2c3d4e5f6",
  "max_results": 1000,
  "output_file": "delhi_interior.csv",
  "business_urls": ["url1", "url2", "..."],
  "processed_indices": [0, 1, 2, 5, 6, 8, ...],
  "last_processed_index": 119,
  "successful_count": 108,
  "failed_count": 12,
  "created_at": "2026-01-31T10:00:00",
  "updated_at": "2026-01-31T10:30:45",
  "completed": false
}
```

### Automatic Backups

- State files are automatically backed up before updates
- Backups stored in `.scraping_state/backups/`
- Timestamped for easy recovery

## How Resume Works (Technical)

1. **Session Start**:
   - Checks for existing state file matching query + max_results
   - If found → loads state and resumes
   - If not found → creates new state

2. **During Scraping**:
   - Each processed URL is marked in state
   - State saved every 5 successful extractions
   - State saved on interruption (Ctrl+C)

3. **On Resume**:
   - Opens existing CSV in append mode
   - Loads already-scraped business names
   - Restores business URLs from state
   - Processes only pending URLs
   - Skips duplicates

4. **On Completion**:
   - Marks state as completed
   - State file kept for reference (can be deleted manually)

## Edge Cases Handled

### Interruption During Scrolling
- If interrupted while loading results, next run will scroll again
- URLs collected before interruption are preserved if extraction started

### Network Errors
- Failed extractions are tracked separately
- Resume will attempt failed URLs again
- Consecutive failures (5+) trigger graceful stop with state save

### File Conflicts
- Resume mode appends to existing file
- Fresh mode overwrites existing file
- State files use hash to avoid conflicts between different queries

### Duplicate Business Names
- Case-insensitive name matching
- Handles "N/A" names properly
- Prevents duplicate entries even across sessions

## Monitoring Progress

### During Scraping

```
Loading results: 100%|███████████████| 350/1000 [02:15<00:00, 2.58it/s]
Extracting & saving:  34%|███▌      | 120/350 [11:24<22:30,  5.87s/it]
```

### In Logs

```
2026-01-31 10:30:45 - INFO - 🔄 Resuming previous session
2026-01-31 10:30:45 - INFO -    Already processed: 120/350
2026-01-31 10:30:45 - INFO -    Output file: delhi_interior.csv
2026-01-31 10:30:50 - INFO - Saved business 121/350: XYZ Interiors
```

## Performance Improvements

### Scrolling Optimization
- **Before**: 20 attempts, stopped at ~120 results
- **After**: 50 attempts with better timing, can load 300-500+ results
- **Note**: Google Maps may still have limits based on search query

### State Saves
- Throttled saves (every 5 records) to reduce I/O
- Atomic writes using temp files
- Automatic backups prevent data loss

### Memory Efficiency
- Business URLs collected upfront, not stored in memory
- Incremental CSV writing
- Set-based tracking for O(1) duplicate checks

## Troubleshooting

### "No existing state found"
- State is query + max_results specific
- Changing either creates a new session
- Use `--show-sessions` to see active sessions

### "Failed to load state"
- State file may be corrupted
- Check backups in `.scraping_state/backups/`
- Delete corrupted state and start fresh

### Resume not working
- Ensure exact same query and max_results
- Check that output filename matches
- Verify `.scraping_state/` directory exists

### Too many duplicates
- State file might be out of sync
- Delete state and restart with `--no-resume`

## Best Practices

1. **Consistent Commands**: Use exact same query and max_results for resume
2. **Monitor Progress**: Use `--show-sessions` to check active sessions
3. **Network Stability**: Resume is designed for network interruptions
4. **Cleanup**: Delete completed state files periodically
5. **Backups**: State backups are automatic, but backup CSV files manually

## Architecture

### Components

1. **StateManager** (`state_service.py`)
   - Manages state persistence
   - Handles atomic saves
   - Creates backups

2. **ScrapingState** (dataclass)
   - Tracks session state
   - Progress calculations
   - URL management

3. **ExportService** (updated)
   - Resume-aware CSV writing
   - Duplicate detection
   - Append mode support

4. **DataExtractorV3** (updated)
   - Resume from specific index
   - Callback includes index
   - Skip processed URLs

5. **GoogleMapsScraper** (updated)
   - State integration
   - Progress tracking
   - Error recovery

## Examples

### Example 1: Large Dataset with Interruptions

```bash
# Start scraping 1000 results
python main.py --query "Interior Designers in New Delhi" --max-results 1000 --output delhi.csv

# Stops at 120 (or you press Ctrl+C)
# Progress: 120/350 businesses extracted

# Resume - just run the same command
python main.py --query "Interior Designers in New Delhi" --max-results 1000 --output delhi.csv

# Continues from 121, appends to delhi.csv
# Final: 350 businesses in delhi.csv
```

### Example 2: Multiple Concurrent Projects

```bash
# Project 1: Interior designers
python main.py --query "Interior Designers in Delhi" --max-results 1000 --output delhi_interior.csv

# Project 2: Coffee shops (different query)
python main.py --query "Coffee Shops in Mumbai" --max-results 500 --output mumbai_coffee.csv

# Both have separate state files, can resume independently
```

### Example 3: Force Fresh Start

```bash
# Start fresh, ignoring any previous state
python main.py --query "Restaurants in NYC" --max-results 500 --output nyc_restaurants.csv --no-resume
```

## Migration from Old Version

If you have existing CSV files:
1. Old CSV files are compatible
2. Resume will append to them
3. State will be created on first run with resume enabled
4. Duplicate detection prevents re-scraping same businesses

## Future Enhancements

Potential improvements:
- [ ] Web UI for session management
- [ ] Pause/Resume specific sessions by ID
- [ ] Export state to shareable format
- [ ] Distributed scraping with shared state
- [ ] Automatic retry for failed URLs
- [ ] Progress notifications

## Credits

This feature uses:
- **Atomic file operations** for safe state saves
- **Dataclasses** for clean state representation
- **Context managers** for resource management
- **Set-based tracking** for O(1) duplicate detection
- **MD5 hashing** for unique session identification
