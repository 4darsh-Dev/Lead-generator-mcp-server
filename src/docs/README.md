# Source Code Architecture

This directory contains the modular implementation of the Google Maps Lead Generator.

## Module Overview

### Core Modules

#### `config.py`
Central configuration module containing all constants and settings.
- Browser configuration
- User agents for rotation
- HTTP headers
- Scraping parameters
- CSS selectors
- Lead scoring rules
- Export settings

#### `logger.py`
Logging configuration and utilities.
- Centralized logging setup
- Consistent log formatting
- Logger factory function

#### `browser.py`
Browser automation and management.
- `BrowserManager`: Handles Playwright browser lifecycle
- Navigation control
- Scroll automation
- Element interaction
- Error recovery

#### `extractor.py`
Data extraction from web pages.
- `DataExtractor`: Extracts individual business fields
- `BusinessDataCollector`: Orchestrates extraction from multiple listings
- Handles missing data gracefully
- Implements retry logic

#### `validator.py`
Data validation and quality scoring.
- `PhoneValidator`: Validates and formats phone numbers
- `WebsiteValidator`: Checks website accessibility
- `LeadScorer`: Calculates lead quality scores (0-100)
- `DataValidator`: Coordinates all validation

#### `exporter.py`
Data export functionality.
- `CSVExporter`: Exports data to CSV format
- `DataExporter`: Main exporter with format support
- Automatic filename generation
- Data sorting and formatting

#### `scraper_core.py`
Main scraper orchestrator.
- `GoogleMapsScraper`: Coordinates entire workflow
- Manages module interactions
- Error handling and cleanup
- Factory function for easy instantiation

#### `cli.py`
Command-line interface.
- Argument parsing and validation
- User-friendly error messages
- Progress reporting
- Entry point for CLI usage

### Supporting Files

#### `mcp-server.py`
Model Context Protocol server implementation.
- Exposes scraping as MCP tool
- HTTP server on port 8080
- Integration with AI assistants

#### `scraper_legacy.py`
Original monolithic implementation (backup).
- Kept for reference
- Not used in production

## Architecture Principles

### Separation of Concerns
Each module has a single, well-defined responsibility:
- Browser operations in `browser.py`
- Data extraction in `extractor.py`
- Validation in `validator.py`
- Export in `exporter.py`

### Dependency Injection
Components receive dependencies through constructors, making testing and modification easier.

### Configuration Management
All constants centralized in `config.py`, eliminating magic numbers and making changes easy.

### Error Handling
Each module handles its own errors and logs appropriately, with graceful degradation.

### Logging
Consistent logging across all modules using centralized logger configuration.

## Data Flow

```
CLI Input
    |
    v
GoogleMapsScraper (scraper_core.py)
    |
    +-> BrowserManager (browser.py)
    |       |
    |       +-> Navigate to Google Maps
    |       +-> Scroll to load results
    |       +-> Click business listings
    |       +-> Navigate between pages
    |
    +-> BusinessDataCollector (extractor.py)
    |       |
    |       +-> DataExtractor
    |               |
    |               +-> Extract name, category, address
    |               +-> Extract phone, website, rating, reviews
    |
    +-> DataValidator (validator.py)
    |       |
    |       +-> PhoneValidator
    |       +-> WebsiteValidator
    |       +-> LeadScorer
    |
    +-> DataExporter (exporter.py)
            |
            +-> CSVExporter
                    |
                    +-> Format DataFrame
                    +-> Sort by lead score
                    +-> Write to CSV
```

## Usage Examples

### Using Individual Modules

```python
from src.browser import BrowserManager
from src.extractor import BusinessDataCollector
from src.validator import DataValidator
from src.exporter import DataExporter

browser = BrowserManager(headless=True)
browser.start()
browser.navigate_to_search("coffee shops in Seattle")

collector = BusinessDataCollector(browser)
data = collector.collect_from_listings(max_results=50)

validator = DataValidator()
validated = validator.validate_batch(data)

exporter = DataExporter()
exporter.export_csv(validated, "output.csv")

browser.close()
```

### Using the Main Scraper

```python
from src.scraper_core import create_scraper

scraper = create_scraper(headless=True)
output_file = scraper.scrape(
    query="restaurants in NYC",
    max_results=100,
    output_file="nyc_restaurants.csv"
)
```

### Using the CLI

```bash
python main.py --query "beauty salons in London" --max-results 100
```

## Extension Points

### Adding New Validators

Add validator class to `validator.py`:

```python
class CustomValidator:
    @staticmethod
    def validate(data):
        # Custom validation logic
        pass
```

Register in `DataValidator.__init__()`.

### Adding Export Formats

Add exporter class to `exporter.py`:

```python
class JSONExporter:
    @staticmethod
    def export(data, filename):
        # JSON export logic
        pass
```

Register in `DataExporter.export()`.

### Customizing Lead Scoring

Modify `LEAD_SCORING` in `config.py` or extend `LeadScorer` class in `validator.py`.

### Adding New Selectors

Update `SELECTORS` dict in `config.py` if Google Maps HTML changes.

## Testing Strategy

### Unit Tests
Test individual components in isolation:
- Validators with known inputs
- Exporters with sample data
- Configuration loading

### Integration Tests
Test module interactions:
- Browser + Extractor
- Validator + Exporter
- Complete workflow

### End-to-End Tests
Test full scraping workflow with real searches (limit to small result sets).

## Maintenance Guidelines

### When Google Maps Changes
1. Update selectors in `config.py`
2. Test extraction with `--visible` flag
3. Update extractor methods if needed

### Adding Features
1. Identify appropriate module
2. Add functionality following existing patterns
3. Update configuration if needed
4. Document in module docstring

### Performance Optimization
1. Adjust delays in `SCRAPING_CONFIG`
2. Optimize DataFrame operations in exporter
3. Consider parallel processing for validation

## Dependencies

See `requirements.txt` in project root:
- playwright: Browser automation
- pandas: Data manipulation
- phonenumbers: Phone validation
- requests: HTTP requests
- tqdm: Progress bars
- mcp: Model Context Protocol

## File Sizes

Approximate lines of code per module:
- config.py: ~100 lines
- logger.py: ~50 lines
- browser.py: ~200 lines
- extractor.py: ~250 lines
- validator.py: ~200 lines
- exporter.py: ~100 lines
- scraper_core.py: ~150 lines
- cli.py: ~150 lines
- mcp-server.py: ~60 lines

Total: ~1,260 lines (vs 500 lines in monolithic version)

## Benefits of Modular Architecture

1. **Maintainability**: Easy to locate and fix bugs
2. **Testability**: Each module can be tested independently
3. **Reusability**: Modules can be used in different contexts
4. **Scalability**: Easy to add new features without breaking existing code
5. **Readability**: Clear structure and responsibilities
6. **Collaboration**: Multiple developers can work on different modules
7. **Configuration**: Centralized settings make changes easy
8. **Error Isolation**: Issues in one module don't cascade
