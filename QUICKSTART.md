# Quick Start Guide

## 🚀 5-Minute Setup

### 1. Install

```bash
# Clone repo
git clone https://github.com/4darsh-Dev/Lead-generator-mcp-server.git
cd Lead-generator-mcp-server

# Setup environment
python -m venv myenv
source myenv/bin/activate  # Windows: myenv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium
```

### 2. Run Your First Scrape

```bash
python src/scraper.py --query "coffee shops in Seattle" --max-results 20 --visible
```

### 3. Check Results

Look for `business_leads_YYYYMMDD_HHMMSS.csv` in your directory.

## 📖 Common Use Cases

### Web Development Leads

```bash
# Find businesses without websites
python src/scraper.py --query "yoga studios in Austin" --max-results 50
```

### Local Service Providers

```bash
# Plumbers, electricians, contractors
python src/scraper.py --query "HVAC contractors in Phoenix" --max-results 100
```

### Restaurants & Hospitality

```bash
python src/scraper.py --query "restaurants in New York" --max-results 200
```

### B2B Sales

```bash
python src/scraper.py --query "software companies in San Francisco" --max-results 150
```

## 🎯 Pro Tips

1. **Start Small**: Test with `--max-results 10` first
2. **Use Visible Mode**: Add `--visible` to debug issues
3. **Be Specific**: "beauty salons in London" > "salons"
4. **Check Lead Scores**: High scores = better leads
5. **Batch Process**: Run multiple queries in sequence

## 🛠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| Import errors | Run `pip install -r requirements.txt` |
| Browser not found | Run `playwright install chromium` |
| No results | Use `--visible` to see what's happening |
| Slow scraping | Normal - respects rate limits |

## 📊 Understanding Output

```csv
name,category,address,phone,phone_valid,website,website_valid,rating,reviews,lead_score
"Joe's Cafe","Coffee shop","123 Main St","+1 206-555-0123",True,"N/A",False,4.8,342,85
```

- **lead_score**: 85 = excellent lead (no website!)
- **phone_valid**: True = verified phone number
- **website_valid**: False = website doesn't exist (opportunity!)

## 🔄 MCP Server Mode

```bash
# Start server
python src/mcp-server.py

# Server runs on http://localhost:8080
# Use with AI assistants or automation tools
```

## 📚 Next Steps

- Read full [README.md](README.md) for detailed documentation
- Check [CONTRIBUTING.md](CONTRIBUTING.md) to contribute
- See [examples/](examples/) for more use cases

---

**Questions?** [Open an issue](https://github.com/4darsh-Dev/Lead-generator-mcp-server/issues)
