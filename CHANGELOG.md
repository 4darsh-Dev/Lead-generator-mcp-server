# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Add proxy support for better anonymity
- Implement unit tests
- Docker containerization
- Additional export formats (JSON, Excel)
- Batch processing for multiple queries

## [1.0.0] - 2026-01-27

### Added
- Initial release
- Google Maps scraping functionality using Playwright
- MCP (Model Context Protocol) server integration
- Intelligent lead scoring algorithm (0-100 scale)
- Phone number validation using phonenumbers library
- Website URL validation with HTTP checks
- International phone number formatting
- CSV export with sorted results
- Anti-detection features:
  - User-agent rotation
  - Random delays
  - Human-like scrolling behavior
- Progress tracking with tqdm
- Command-line interface with argparse
- Comprehensive documentation
- Error handling and recovery mechanisms

### Features
- Search any business type on Google Maps
- Extract: name, category, address, phone, website, rating, reviews
- Validate phone numbers and websites
- Score leads based on multiple factors
- Export to CSV sorted by lead quality
- Headless and visible browser modes
- Configurable max results limit
- Custom output filenames

### Documentation
- Comprehensive README.md
- Installation instructions
- Usage examples
- Architecture overview
- API documentation
- Contributing guidelines
- MIT License

## [0.1.0] - 2025-XX-XX

### Initial Development
- Basic scraping prototype
- Selenium-based implementation (later migrated to Playwright)
- Core data extraction logic

---

## Version History

- **1.0.0** - First stable release with MCP server
- **0.1.0** - Initial development version

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.
