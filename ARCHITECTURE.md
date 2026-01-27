# Project Structure Documentation

## Directory Layout

```
Lead-generator-mcp-server/
├── README.md                    Main documentation
├── QUICKSTART.md               Quick start guide
├── CONTRIBUTING.md             Contribution guidelines
├── CHANGELOG.md                Version history
├── EXAMPLES.md                 Usage examples
├── LICENSE                     MIT License
├── .gitignore                  Git ignore rules
├── requirements.txt            Python dependencies
├── main.py                     CLI entry point
│
├── src/                        Source code
│   ├── __init__.py            Package initialization
│   ├── README.md              Architecture documentation
│   ├── config.py              Configuration constants
│   ├── logger.py              Logging utilities
│   ├── browser.py             Browser automation
│   ├── extractor.py           Data extraction
│   ├── validator.py           Data validation
│   ├── exporter.py            Data export
│   ├── scraper_core.py        Main orchestrator
│   ├── cli.py                 Command-line interface
│   ├── mcp-server.py          MCP server
│   └── scraper_legacy.py      Legacy monolithic code (backup)
│
└── myenv/                      Virtual environment (not in git)
```

## Module Responsibilities

| Module | Responsibility | Key Classes |
|--------|---------------|-------------|
| `config.py` | Configuration constants | SELECTORS, SCRAPING_CONFIG, LEAD_SCORING |
| `logger.py` | Logging setup | get_logger(), configure_logging() |
| `browser.py` | Browser automation | BrowserManager |
| `extractor.py` | Data extraction | DataExtractor, BusinessDataCollector |
| `validator.py` | Data validation | PhoneValidator, WebsiteValidator, LeadScorer, DataValidator |
| `exporter.py` | Data export | CSVExporter, DataExporter |
| `scraper_core.py` | Workflow orchestration | GoogleMapsScraper, create_scraper() |
| `cli.py` | CLI interface | parse_arguments(), run_cli() |
| `mcp-server.py` | MCP server | scrape_google_maps() tool |

## Design Patterns Used

### 1. Factory Pattern
`create_scraper()` function in `scraper_core.py` provides a clean way to instantiate scraper with configuration.

### 2. Strategy Pattern
Validators and exporters can be swapped out without changing core logic.

### 3. Facade Pattern
`GoogleMapsScraper` provides a simple interface hiding complex interactions between modules.

### 4. Single Responsibility Principle
Each module and class has one clear purpose.

### 5. Dependency Injection
Components receive dependencies through constructors, not hard-coded imports.

### 6. Configuration as Code
All settings centralized in `config.py` for easy modification.

## Data Models

### Business Data Dictionary

```python
{
    'name': str,              # Business name
    'category': str,          # Business type/category
    'address': str,           # Full address
    'phone': str,             # Phone number (formatted)
    'phone_valid': bool,      # Phone validation result
    'website': str,           # Website URL
    'website_valid': bool,    # Website accessibility
    'rating': str,            # Google rating (0-5)
    'reviews': str,           # Number of reviews
    'lead_score': int         # Quality score (0-100)
}
```

## Execution Flow

### 1. CLI Execution (main.py)
```
main.py
  └─> cli.run_cli()
        ├─> parse_arguments()
        ├─> validate_arguments()
        └─> create_scraper()
              └─> GoogleMapsScraper.scrape()
```

### 2. MCP Server Execution (mcp-server.py)
```
mcp-server.py
  └─> FastMCP.run()
        └─> scrape_google_maps() tool
              ├─> create_scraper()
              └─> Manual workflow execution
```

### 3. Scraping Workflow (scraper_core.py)
```
GoogleMapsScraper.scrape()
  ├─> BrowserManager.start()
  ├─> BrowserManager.navigate_to_search()
  ├─> BrowserManager.scroll_results_container()
  ├─> BusinessDataCollector.collect_from_listings()
  │     └─> DataExtractor.extract_all() (for each business)
  ├─> DataValidator.validate_batch()
  │     ├─> PhoneValidator.validate()
  │     ├─> WebsiteValidator.validate()
  │     └─> LeadScorer.calculate_score()
  ├─> DataExporter.export_csv()
  └─> BrowserManager.close()
```

## Configuration Files

### config.py Sections

1. **BROWSER_CONFIG**: Browser settings (headless, viewport)
2. **USER_AGENTS**: Rotation list for anti-detection
3. **HTTP_HEADERS**: Request headers
4. **SCRAPING_CONFIG**: Timing, delays, timeouts
5. **SELECTORS**: CSS selectors for Google Maps
6. **LEAD_SCORING**: Scoring algorithm parameters
7. **VALIDATION_CONFIG**: Validation settings
8. **EXPORT_CONFIG**: Export format settings
9. **GOOGLE_MAPS_CONFIG**: Google Maps URL patterns

## Error Handling Strategy

### Levels of Error Handling

1. **Field Level**: Missing fields default to "N/A"
2. **Business Level**: Failed extraction logged, business skipped
3. **Page Level**: Navigation failures trigger retry
4. **Workflow Level**: Complete failure reported to user

### Recovery Mechanisms

- Failed click: Go back and continue with next business
- Failed navigation: Retry search query
- Timeout: Skip and continue
- No results: Log warning and exit gracefully

## Performance Considerations

### Bottlenecks

1. **Network requests**: Limited by Google Maps rate limiting
2. **Page loading**: Wait times for dynamic content
3. **Website validation**: HTTP requests for each URL
4. **Scrolling**: Multiple scroll operations to load results

### Optimizations

1. **Parallel validation**: Could validate websites concurrently
2. **Caching**: Could cache validation results
3. **Batch operations**: DataFrame operations are vectorized
4. **Smart delays**: Random delays only where needed

## Extension Examples

### Example 1: Add JSON Export

```python
# In exporter.py

import json

class JSONExporter:
    @staticmethod
    def export(data, filename):
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        return filename

# In DataExporter class
def export_json(self, data, filename=None):
    if not filename:
        filename = f"leads_{datetime.now():%Y%m%d}.json"
    return JSONExporter.export(data, filename)
```

### Example 2: Add Email Extraction

```python
# In extractor.py

def extract_email(self):
    try:
        # Look for email in page content
        page_text = self.page.inner_text()
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', page_text)
        if email_match:
            return email_match.group(0)
    except Exception as e:
        logger.warning(f"Error extracting email: {e}")
    return "N/A"

# In extract_all() method, add:
'email': self.extract_email(),
```

### Example 3: Add Proxy Support

```python
# In config.py
PROXY_CONFIG = {
    'enabled': False,
    'server': 'http://proxy.example.com:8080',
    'username': None,
    'password': None
}

# In browser.py BrowserManager.start()
if PROXY_CONFIG['enabled']:
    self.browser = self.playwright.chromium.launch(
        headless=self.headless,
        proxy={'server': PROXY_CONFIG['server']}
    )
```

## Testing Guidelines

### Unit Tests Structure

```
tests/
├── test_config.py          # Configuration loading
├── test_validators.py      # Validation functions
├── test_extractors.py      # Extraction logic
├── test_exporters.py       # Export functionality
└── test_integration.py     # End-to-end tests
```

### Example Unit Test

```python
import unittest
from src.validator import PhoneValidator

class TestPhoneValidator(unittest.TestCase):
    def setUp(self):
        self.validator = PhoneValidator('US')
    
    def test_valid_us_phone(self):
        phone, valid = self.validator.validate('(206) 555-0123')
        self.assertTrue(valid)
        self.assertIn('+1', phone)
    
    def test_invalid_phone(self):
        phone, valid = self.validator.validate('invalid')
        self.assertFalse(valid)
```

## Deployment Options

### 1. Standalone Script
```bash
python main.py --query "..."
```

### 2. MCP Server
```bash
python src/mcp-server.py
```

### 3. Docker Container
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install chromium
COPY src/ ./src/
COPY main.py .
CMD ["python", "main.py"]
```

### 4. Scheduled Job
```bash
# crontab
0 2 * * * cd /path/to/project && python main.py --query "daily query" >> logs/scraper.log 2>&1
```

## Versioning

Following Semantic Versioning (MAJOR.MINOR.PATCH):
- MAJOR: Incompatible API changes
- MINOR: New functionality (backwards compatible)
- PATCH: Bug fixes (backwards compatible)

Current version: 1.0.0 (see `src/__init__.py`)

## Contributing Workflow

1. Fork repository
2. Create feature branch
3. Implement changes in appropriate module(s)
4. Update tests
5. Update documentation
6. Submit pull request

## License

MIT License - see LICENSE file
