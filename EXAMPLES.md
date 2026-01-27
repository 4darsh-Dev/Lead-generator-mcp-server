# Example Queries & Use Cases

This file contains real-world examples for different industries and use cases.

## 🍕 Food & Beverage

### Restaurants
```bash
python src/scraper.py --query "italian restaurants in Boston" --max-results 100
python src/scraper.py --query "sushi bars in Los Angeles" --max-results 75
python src/scraper.py --query "vegan restaurants in Portland" --max-results 50
```

### Cafes & Coffee Shops
```bash
python src/scraper.py --query "coffee shops in Seattle" --max-results 150
python src/scraper.py --query "tea houses in San Francisco" --max-results 50
```

### Bars & Nightlife
```bash
python src/scraper.py --query "cocktail bars in Miami" --max-results 80
python src/scraper.py --query "craft breweries in Denver" --max-results 60
```

## 💇 Beauty & Wellness

### Salons & Spas
```bash
python src/scraper.py --query "beauty salons in London" --max-results 200
python src/scraper.py --query "nail salons in New York" --max-results 150
python src/scraper.py --query "day spas in Los Angeles" --max-results 100
```

### Fitness & Yoga
```bash
python src/scraper.py --query "yoga studios in Austin" --max-results 75
python src/scraper.py --query "gyms in Chicago" --max-results 120
python src/scraper.py --query "pilates studios in Miami" --max-results 50
```

### Medical & Dental
```bash
python src/scraper.py --query "dentists in Phoenix" --max-results 100
python src/scraper.py --query "chiropractors in Seattle" --max-results 80
python src/scraper.py --query "physical therapy clinics in Dallas" --max-results 60
```

## 🏠 Home Services

### Contractors
```bash
python src/scraper.py --query "plumbers in Boston" --max-results 150
python src/scraper.py --query "electricians in Houston" --max-results 120
python src/scraper.py --query "HVAC contractors in Phoenix" --max-results 100
```

### Home Improvement
```bash
python src/scraper.py --query "landscaping companies in Atlanta" --max-results 80
python src/scraper.py --query "roofing contractors in Denver" --max-results 70
python src/scraper.py --query "painting services in Chicago" --max-results 90
```

### Cleaning Services
```bash
python src/scraper.py --query "house cleaning services in Seattle" --max-results 100
python src/scraper.py --query "carpet cleaning in San Diego" --max-results 60
```

## 💼 Professional Services

### Legal & Financial
```bash
python src/scraper.py --query "law firms in New York" --max-results 150
python src/scraper.py --query "accountants in San Francisco" --max-results 100
python src/scraper.py --query "financial advisors in Boston" --max-results 80
```

### Real Estate
```bash
python src/scraper.py --query "real estate agents in Miami" --max-results 200
python src/scraper.py --query "property management companies in Austin" --max-results 75
```

### Marketing & Design
```bash
python src/scraper.py --query "digital marketing agencies in Toronto" --max-results 100
python src/scraper.py --query "web design companies in Seattle" --max-results 80
python src/scraper.py --query "graphic designers in Los Angeles" --max-results 60
```

## 🚗 Automotive

```bash
python src/scraper.py --query "auto repair shops in Detroit" --max-results 150
python src/scraper.py --query "car dealerships in Houston" --max-results 100
python src/scraper.py --query "tire shops in Phoenix" --max-results 80
```

## 🛒 Retail

```bash
python src/scraper.py --query "boutique clothing stores in New York" --max-results 120
python src/scraper.py --query "book stores in Portland" --max-results 50
python src/scraper.py --query "pet stores in San Diego" --max-results 70
```

## 🏨 Hospitality & Travel

```bash
python src/scraper.py --query "hotels in Las Vegas" --max-results 150
python src/scraper.py --query "travel agencies in Miami" --max-results 60
python src/scraper.py --query "bed and breakfast in Napa Valley" --max-results 40
```

## 🎓 Education

```bash
python src/scraper.py --query "tutoring centers in Boston" --max-results 80
python src/scraper.py --query "music schools in Nashville" --max-results 50
python src/scraper.py --query "dance studios in Los Angeles" --max-results 70
```

## 💻 Technology

```bash
python src/scraper.py --query "software companies in San Francisco" --max-results 200
python src/scraper.py --query "IT support services in Seattle" --max-results 100
python src/scraper.py --query "computer repair shops in Austin" --max-results 60
```

## 🌍 International Searches

### United Kingdom
```bash
python src/scraper.py --query "coffee shops in Manchester" --max-results 100
python src/scraper.py --query "restaurants in Edinburgh" --max-results 80
```

### India
```bash
python src/scraper.py --query "cafes in Mumbai" --max-results 150
python src/scraper.py --query "fashion boutiques in New Delhi" --max-results 100
```

### Australia
```bash
python src/scraper.py --query "surf shops in Sydney" --max-results 60
python src/scraper.py --query "restaurants in Melbourne" --max-results 120
```

### Canada
```bash
python src/scraper.py --query "sushi restaurants in Vancouver" --max-results 80
python src/scraper.py --query "gyms in Toronto" --max-results 100
```

## 🎯 Lead Generation Strategies

### Strategy 1: Target Businesses Without Websites
```bash
# These typically score highest (70-90)
python src/scraper.py --query "local restaurants in rural areas" --max-results 50
```

### Strategy 2: New Businesses (Few Reviews)
```bash
# Look for businesses with <10 reviews
python src/scraper.py --query "new yoga studios in trendy neighborhoods" --max-results 50
```

### Strategy 3: High-Quality Businesses
```bash
# Target 4.5+ star businesses that might need better digital presence
python src/scraper.py --query "highly rated but small salons" --max-results 100
```

### Strategy 4: Bulk Lead Generation
```bash
# Run multiple queries in sequence
python src/scraper.py --query "dentists in Chicago" --max-results 200 --output chicago_dentists.csv
python src/scraper.py --query "dentists in Boston" --max-results 200 --output boston_dentists.csv
python src/scraper.py --query "dentists in Seattle" --max-results 200 --output seattle_dentists.csv
```

## 📊 Output Analysis Tips

1. **Sort by lead_score** - Focus on 70+ scores first
2. **Filter by phone_valid** - Prioritize verified contacts
3. **Target "N/A" websites** - Best conversion potential
4. **Check review count** - <50 reviews = newer business
5. **Geographic clustering** - Group by city/neighborhood

## 🔄 Batch Processing Script

Create a bash script for multiple queries:

```bash
#!/bin/bash
# scrape_multiple.sh

queries=(
    "coffee shops in Seattle"
    "restaurants in Portland"
    "gyms in Austin"
)

for query in "${queries[@]}"; do
    echo "Scraping: $query"
    python src/scraper.py --query "$query" --max-results 100
    sleep 60  # 1 minute delay between queries
done
```

Run with: `chmod +x scrape_multiple.sh && ./scrape_multiple.sh`

## 💡 Pro Tips

1. **Be Specific**: "vegan bakeries" > "bakeries"
2. **Use Locations**: Always include city/area
3. **Start Small**: Test with 10-20 results first
4. **Respect Limits**: Don't scrape thousands at once
5. **Verify Data**: Always manually check a sample

---

**Need more examples?** [Open an issue](https://github.com/4darsh-Dev/Lead-generator-mcp-server/issues) with your use case!
