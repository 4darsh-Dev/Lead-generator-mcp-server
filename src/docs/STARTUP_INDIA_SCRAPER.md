# Startup India Scaling Scraper

This workflow scrapes Startup India startup profiles from the search page while **enforcing filters**:

- `roles=Startup`
- `stages=scaling`

Implementation is in `src/startup_india` and supports:

- async profile extraction with configurable concurrency
- load-more listing discovery until no new cards
- incremental CSV append mode (flush + fsync per row)
- composite dedupe key: `name + city + state + website`
- checkpoint/resume state in `.scraping_state/startup_india`

## Run

```bash
python main.py \
  --startup-india \
  --search-url "https://www.startupindia.gov.in/content/sih/en/search.html?stages=scaling&roles=Startup&page=1" \
  --max-results 14000 \
  --output startup_india_scaling.csv \
  --concurrency 5 \
  --checkpoint-interval 20
```

## Important flags

- `--startup-india`: enables Startup India pipeline
- `--search-url`: base search URL (filters are auto-corrected)
- `--max-results`: cap on number of profiles to process (must be `>= 1`)
- `--concurrency`: concurrent profile fetches
- `--checkpoint-interval`: state save frequency
- `--max-retries`: retries per profile page
- `--no-resume`: ignore existing state and start fresh

## Output columns

- `name`
- `stage`
- `city`
- `state`
- `industry`
- `phone`
- `email`
- `website`
- `description`
- `engagement_level`
- `active_since`
- `profile_url`
- `listing_url`
- `run_id`
- `scraped_at`
