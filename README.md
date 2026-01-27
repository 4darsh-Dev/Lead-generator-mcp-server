# 🎯 Lead Generator MCP Server

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Playwright](https://img.shields.io/badge/playwright-1.51.0-brightgreen.svg)](https://playwright.dev/)
[![MCP](https://img.shields.io/badge/MCP-1.6.0-orange.svg)](https://modelcontextprotocol.io/)

A powerful **Model Context Protocol (MCP) server** and standalone scraper for automated business lead generation from Google Maps. Extract, validate, and score business data to identify high-quality leads for B2B sales, marketing, and outreach campaigns.

## 📋 Table of Contents

- [Features](#-features)
- [How It Works](#-how-it-works)
- [Installation](#-installation)
- [Usage](#-usage)
  - [Standalone Scraper](#1-standalone-scraper-cli)
  - [MCP Server](#2-mcp-server-mode)
- [Configuration](#-configuration)
- [Output Format](#-output-format)
- [Lead Scoring Algorithm](#-lead-scoring-algorithm)
- [Architecture](#-architecture)
- [Anti-Detection Features](#-anti-detection-features)
- [Contributing](#-contributing)
- [License](#-license)
- [Disclaimer](#%EF%B8%8F-disclaimer)

## ✨ Features

- 🔍 **Automated Google Maps Scraping** - Extract business data from search queries
- 🤖 **MCP Server Integration** - Expose scraping functionality via Model Context Protocol
- 📊 **Intelligent Lead Scoring** - Rate businesses based on website presence, reviews, and ratings
- ✅ **Data Validation** - Verify phone numbers and website URLs
- 🌐 **International Phone Formatting** - Standardize phone numbers using Google's libphonenumber
- 🎭 **Anti-Detection Mechanisms** - User-agent rotation, random delays, human-like behavior
- 📈 **Progress Tracking** - Real-time progress bars with tqdm
- 💾 **CSV Export** - Structured data output sorted by lead quality
- 🔄 **Error Recovery** - Robust error handling with automatic retries

## 🎯 How It Works

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│   Search    │────>│ Scroll &     │────>│  Extract    │────>│  Validate &  │
│   Query     │     │ Load Results │     │  Data       │     │  Score Leads │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘
                                                                      │
                                                                      ▼
                                                               ┌──────────────┐
                                                               │ Export CSV   │
                                                               └──────────────┘
```

1. **Search**: Navigate to Google Maps with your query
2. **Scroll**: Dynamically load results by scrolling (handles infinite scroll)
3. **Extract**: Click each business listing and scrape details
4. **Validate**: Verify phone numbers and websites
5. **Score**: Calculate lead quality score (0-100)
6. **Export**: Save to CSV sorted by lead score

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Step 1: Clone the Repository

```bash
git clone https://github.com/4darsh-Dev/Lead-generator-mcp-server.git
cd Lead-generator-mcp-server
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv myenv

# Activate virtual environment
# On Linux/macOS:
source myenv/bin/activate

# On Windows:
myenv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# Install Playwright browsers (required)
playwright install chromium
```

## 📖 Usage

### 1. Standalone Scraper (CLI)

#### Basic Usage

```bash
python src/scraper.py --query "coffee shops in Seattle" --max-results 50
```

#### Advanced Options

```bash
# Visible browser mode (for debugging)
python src/scraper.py --query "beauty salons in London" --max-results 100 --visible

# Custom output filename
python src/scraper.py --query "restaurants in New York" --max-results 200 --output ny_restaurants.csv

# Complete example
python src/scraper.py \
  --query "plumbers in Boston" \
  --max-results 150 \
  --output boston_plumbers_2026.csv \
  --visible
```

#### Command Line Arguments

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `--query` | string | ✅ Yes | - | Search query (e.g., "dentists in Chicago") |
| `--max-results` | integer | ❌ No | 100 | Maximum number of businesses to scrape |
| `--output` | string | ❌ No | `business_leads_{timestamp}.csv` | Output CSV filename |
| `--visible` | flag | ❌ No | False | Run browser in visible mode (headless=False) |

#### Example Queries

```bash
# Target businesses without websites (good for web dev services)
python src/scraper.py --query "yoga studios in Austin"

# B2B lead generation
python src/scraper.py --query "software companies in San Francisco" --max-results 300

# Local service businesses
python src/scraper.py --query "HVAC contractors in Phoenix" --max-results 150

# International search
python src/scraper.py --query "cafes in Mumbai" --max-results 100
```

### 2. MCP Server Mode

Run as an MCP server to integrate with AI assistants and automation tools:

```bash
python src/mcp-server.py
```

The server will start on `http://localhost:8080` and expose the `scrape_google_maps` tool.

#### MCP Tool Usage

```python
# Example MCP tool call
result = scrape_google_maps(
    query="digital marketing agencies in Toronto",
    max_results=50
)
# Returns: List of validated business data dictionaries
```

## ⚙️ Configuration

### Headless Mode

```python
# In your code
scraper = GoogleMapsScraper(headless=True)  # Invisible (faster)
scraper = GoogleMapsScraper(headless=False)  # Visible (debugging)
```

### Slow Motion (for debugging)

```python
# Add delays between actions (milliseconds)
scraper = GoogleMapsScraper(headless=False, slow_mo=100)
```

### User Agents

User agents are rotated automatically from the `USER_AGENTS` list in `scraper.py`. You can add more:

```python
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
    # Add your custom user agents here
]
```

## 📊 Output Format

### CSV Columns

| Column | Type | Description |
|--------|------|-------------|
| `name` | string | Business name |
| `category` | string | Business category/type |
| `address` | string | Full address |
| `phone` | string | Phone number (internationally formatted) |
| `phone_valid` | boolean | Phone number validation status |
| `website` | string | Website URL |
| `website_valid` | boolean | Website accessibility status |
| `rating` | float | Google Maps rating (0-5 stars) |
| `reviews` | integer | Number of reviews |
| `lead_score` | integer | Calculated lead quality score (0-100) |

### Example Output

```csv
name,category,address,phone,phone_valid,website,website_valid,rating,reviews,lead_score
"Joe's Coffee Shop","Coffee shop","123 Main St, Seattle, WA","+1 206-555-0123",True,"N/A",False,4.8,342,85
"Brew & Bean","Café","456 Pike St, Seattle, WA","+1 206-555-0456",True,"https://brewbean.com",True,4.5,128,70
```

## 🎯 Lead Scoring Algorithm

Businesses are scored from **0-100** based on:

| Factor | Impact | Points |
|--------|--------|--------|
| **No Website** | High-quality lead for web services | +20 |
| **Invalid Website** | Needs website help | +15 |
| **High Rating (4.5+)** | Quality-focused, has budget | +10 |
| **Low Reviews (<10)** | New business, needs marketing | +10 |
| **Many Reviews (>100)** | Established, has resources | +5 |

**Base Score**: 50 points  
**Max Score**: 100 points

Leads are **automatically sorted** by score (highest first) in the CSV output.

## 🏗️ Architecture

```
Lead-generator-mcp-server/
├── src/
│   ├── scraper.py           # Core scraping logic
│   ├── mcp-server.py        # MCP server wrapper
│   └── __init__.py
├── myenv/                   # Virtual environment
├── requirements.txt         # Python dependencies
├── LICENSE                  # MIT License
└── README.md               # Documentation
```

### Key Components

- **`GoogleMapsScraper` Class**: Main scraper with browser automation
- **`scrape_google_maps()` Tool**: MCP-exposed function
- **Playwright**: Browser automation framework
- **Pandas**: Data manipulation and CSV export
- **phonenumbers**: Phone validation (Google's libphonenumber)
- **tqdm**: Progress bars

## 🎭 Anti-Detection Features

1. **User-Agent Rotation**: Random user agents per session
2. **Human-Like Delays**: Random 1-3 second pauses
3. **Realistic Headers**: Accept-Language, Accept headers
4. **Slow Motion**: Configurable delays between actions
5. **Scroll Behavior**: Smooth scrolling like humans
6. **Error Recovery**: Graceful handling of detection

## 🛠️ Troubleshooting

### Common Issues

**Issue**: `playwright._impl._errors.Error: Executable doesn't exist`  
**Solution**: Run `playwright install chromium`

**Issue**: No results found  
**Solution**: 
- Try running with `--visible` flag to debug
- Check if Google Maps changed their HTML structure
- Verify your internet connection

**Issue**: ImportError for logging/argparse  
**Solution**: Add these imports to `scraper.py`:
```python
import logging
import argparse
import random
import time
import re
import requests
import pandas as pd
import phonenumbers
```

**Issue**: Script hangs during scrolling  
**Solution**: 
- Reduce `--max-results` value
- Check `max_attempts` in `scroll_results()` method

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/Lead-generator-mcp-server.git
cd Lead-generator-mcp-server

# Create virtual environment
python -m venv myenv
source myenv/bin/activate  # or myenv\Scripts\activate on Windows

# Install dev dependencies
pip install -r requirements.txt
playwright install chromium

# Run tests (if available)
pytest tests/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2025 ADARSH MAURYA

## ⚠️ Disclaimer

This tool is for **educational and research purposes only**. When using this scraper:

- ✅ Respect Google Maps Terms of Service
- ✅ Implement rate limiting (don't scrape too fast)
- ✅ Use responsibly for legitimate business purposes
- ✅ Comply with GDPR, CCPA, and data protection laws
- ❌ Don't use for spam or unsolicited marketing
- ❌ Don't overload Google's servers

**The authors are not responsible for misuse of this tool.**

## 📞 Contact & Support

- **Author**: ADARSH MAURYA
- **GitHub**: [@4darsh-Dev](https://github.com/4darsh-Dev)
- **Repository**: [Lead-generator-mcp-server](https://github.com/4darsh-Dev/Lead-generator-mcp-server)

### Issues & Bugs

Found a bug? Have a feature request? [Open an issue](https://github.com/4darsh-Dev/Lead-generator-mcp-server/issues)

---

⭐ **Star this repository** if you find it helpful!

Made with ❤️ by [Adarsh Maurya](https://github.com/4darsh-Dev)
