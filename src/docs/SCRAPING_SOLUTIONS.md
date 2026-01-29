# 🔧 Google Maps Scraping - Solutions & Best Practices

## 📊 Problem Analysis

### Key Issues Identified:

1. **Stale Element References** (PRIMARY)
   - Error: `Protocol error (DOM.describeNode): Cannot find context with specified id`
   - **Cause**: Google Maps is a Single Page Application (SPA) that dynamically updates the DOM
   - **Impact**: Stored element references become invalid after navigation or page updates

2. **Navigation State Corruption**
   - Error: `Page.wait_for_selector: Timeout 10000ms exceeded`
   - **Cause**: Browser back button fails to return to valid search results page
   - **Impact**: Scraper gets stuck in invalid state, causing cascading failures

3. **No Effective Recovery Mechanism**
   - Once failures start at listing #61, all subsequent listings fail
   - Current error recovery doesn't restore valid page state
   - Scraper continues attempting extraction from corrupted state

---

## 🎯 Three Solutions (Best to Good)

### ✅ **Solution 1: Playwright Locators API** (RECOMMENDED)

**File**: `extraction_service_v2.py`

#### Why This Is Best:
- **Modern Playwright best practice** - Uses auto-retrying locators
- **No stale elements** - Locators re-query DOM on each action
- **Auto-waiting** - Built-in waiting for element actionability
- **URL-based navigation** - More reliable than browser back button
- **State validation** - Checks page state before each operation

#### Key Features:
```python
# ✅ Auto-retrying locator (queries fresh each time)
business_links_locator = self.page.locator(SELECTORS['business_link'])
current_link = business_links_locator.nth(i)

# ✅ Auto-waits for visibility and actionability
current_link.scroll_into_view_if_needed(timeout=5000)
current_link.click(timeout=5000)

# ✅ URL-based navigation (not browser back)
self.page.goto(self.search_url, wait_until='domcontentloaded')
```

#### Advantages:
- ✅ Eliminates stale element errors
- ✅ More resilient to DOM changes
- ✅ Better error messages
- ✅ Follows Playwright documentation recommendations
- ✅ Validates page state before operations

#### Disadvantages:
- Slightly more verbose syntax
- Requires understanding of locator API

---

### ✅ **Solution 2: URL-Based Navigation** (VERY RELIABLE)

**File**: `extraction_service_v3.py`

#### Why This Works:
- **Collects all business URLs upfront** - No need to maintain element references
- **Direct URL navigation** - Bypasses click interactions entirely
- **Simple and robust** - Fewer moving parts to break
- **No back navigation** - Eliminates navigation state issues

#### Key Features:
```python
# ✅ Extract all URLs at start
self.business_urls = self._collect_business_urls(max_results)

# ✅ Navigate directly to each business
for business_url in self.business_urls:
    self.page.goto(business_url, wait_until='domcontentloaded')
    # Extract data...
```

#### Advantages:
- ✅ **Completely eliminates stale element issues**
- ✅ No need for back navigation
- ✅ Can restart from any point using URL list
- ✅ Simpler error recovery
- ✅ Can parallelize extraction (future enhancement)

#### Disadvantages:
- Requires initial pass to collect URLs
- May miss dynamically loaded listings
- Slightly more network requests

---

### ⚠️ **Solution 3: Enhanced Current Approach** (MINIMAL CHANGE)

Improvements to your current `extraction_service.py`:

#### Key Changes:
```python
# ❌ OLD: Store element references (becomes stale)
business_links = self.browser.get_business_links(max_results)
for link in business_links:
    link.click()

# ✅ NEW: Query fresh elements each iteration
for i in range(max_results):
    # Get fresh elements each time
    business_links = self.page.query_selector_all(SELECTORS['business_link'])
    if i >= len(business_links):
        break
    
    # Use element immediately
    link = business_links[i]
    link.click()
```

#### Additional Improvements:
1. **Add state validation**:
   ```python
   def _is_on_search_results(self) -> bool:
       try:
           return self.page.query_selector(SELECTORS['business_link']) is not None
       except:
           return False
   ```

2. **Improve navigation recovery**:
   ```python
   def _safe_navigate_back(self) -> bool:
       try:
           # Try standard back
           self.page.go_back()
           self.page.wait_for_selector(SELECTORS['business_link'], timeout=5000)
           return True
       except:
           # Fallback: reload search URL
           if self.search_url:
               self.page.goto(self.search_url)
               return True
           return False
   ```

3. **Add circuit breaker**:
   ```python
   consecutive_failures = 0
   max_consecutive_failures = 3
   
   if consecutive_failures >= max_consecutive_failures:
       logger.error("Circuit breaker triggered - stopping extraction")
       break
   ```

---

## 📋 Comparison Matrix

| Feature | Solution 1 (Locators) | Solution 2 (URLs) | Solution 3 (Enhanced) |
|---------|----------------------|-------------------|----------------------|
| **Prevents stale elements** | ✅ Completely | ✅ Completely | ⚠️ Reduces |
| **Navigation reliability** | ✅ URL-based | ✅ Direct URLs | ⚠️ Browser back |
| **Implementation complexity** | Medium | Low | Very Low |
| **Performance** | Good | Very Good | Good |
| **Maintainability** | Excellent | Excellent | Good |
| **Playwright best practice** | ✅ Yes | ✅ Yes | ❌ No |
| **Recovery from errors** | ✅ Excellent | ✅ Excellent | ⚠️ Fair |
| **Code changes required** | Moderate | Moderate | Minimal |

---

## 🚀 Implementation Recommendation

### **Recommended: Solution 2 (URL-Based Navigation)**

**Why?**
1. **Most reliable** - Completely eliminates stale element issues
2. **Simple to understand** - Straightforward URL-based approach
3. **Easy to debug** - Can inspect/replay individual URLs
4. **Best for your use case** - Google Maps provides stable URLs

### Migration Path:

1. **Immediate fix** (10 minutes):
   ```python
   # Use extraction_service_v3.py
   from src.services.extraction_service_v3 import DataExtractorV3
   
   extractor = DataExtractorV3(browser_manager)
   ```

2. **Test thoroughly**:
   - Run on small batch (10-20 listings)
   - Verify data quality
   - Monitor for errors

3. **Roll out gradually**:
   - Start with low-volume searches
   - Increase to full production load

---

## 🛠️ Additional Best Practices

### 1. **Wait for Network Idle**
```python
self.page.goto(url, wait_until='networkidle')  # Wait for AJAX requests
```

### 2. **Implement Exponential Backoff**
```python
def exponential_backoff(attempt: int, base_delay: float = 1.0) -> float:
    return min(base_delay * (2 ** attempt), 30.0)  # Max 30 seconds
```

### 3. **Use Context Managers**
```python
with self.page.expect_navigation(timeout=10000):
    link.click()
```

### 4. **Add Telemetry**
```python
metrics = {
    'total_attempts': 0,
    'successful_extractions': 0,
    'stale_element_errors': 0,
    'navigation_errors': 0,
    'timeout_errors': 0
}
```

### 5. **Implement Checkpointing**
```python
# Save progress periodically
def save_checkpoint(self, extracted_urls: List[str]):
    with open('checkpoint.json', 'w') as f:
        json.dump({'processed_urls': extracted_urls}, f)
```

---

## 📖 Resources

- [Playwright Locators Documentation](https://playwright.dev/python/docs/locators)
- [Playwright Auto-waiting](https://playwright.dev/python/docs/actionability)
- [Handling SPAs with Playwright](https://playwright.dev/python/docs/navigations)
- [Google Maps URL Structure](https://developers.google.com/maps/documentation/urls/get-started)

---

## 🧪 Testing the Solutions

### Test Script:
```python
# test_extraction_solutions.py
from src.services.extraction_service_v2 import DataExtractorV2
from src.services.extraction_service_v3 import DataExtractorV3
from src.services.browser_service import BrowserManager

def test_solution(extractor_class, name):
    print(f"\n{'='*60}")
    print(f"Testing {name}")
    print('='*60)
    
    browser = BrowserManager(headless=False)
    browser.start()
    
    try:
        browser.navigate_to_search("coffee shops in Delhi")
        browser.scroll_results_container(50)
        
        extractor = extractor_class(browser)
        
        results = []
        def callback(data):
            results.append(data)
            print(f"✅ Extracted: {data['name']}")
        
        count = extractor.extract_from_listings_incremental(
            max_results=50,
            callback=callback
        )
        
        print(f"\n📊 Results: {count} successful out of 50 attempted")
        print(f"📊 Success rate: {(count/50)*100:.1f}%")
        
    finally:
        browser.close()

# Run tests
test_solution(DataExtractorV2, "Solution 1: Playwright Locators")
test_solution(DataExtractorV3, "Solution 2: URL-Based Navigation")
```

---

## 💡 Quick Win: Update Your Current Code

If you want to **minimally modify** your existing code, add these changes to `extraction_service.py`:

```python
# At the start of extract_from_listings_incremental()
self.search_url = self.page.url  # Store search URL

# Replace the main loop with:
for i in range(len(business_links)):
    try:
        # ✅ Get fresh link each iteration
        fresh_links = self.page.query_selector_all(SELECTORS['business_link'])
        if i >= len(fresh_links):
            break
        
        link = fresh_links[i]
        
        # Rest of your code...
        
    except Exception as e:
        # ✅ Better recovery
        logger.error(f"Error on listing {i+1}: {e}")
        try:
            # Try URL-based recovery
            self.page.goto(self.search_url, timeout=10000)
            time.sleep(2)
        except:
            logger.error("Recovery failed")
            break
```

---

## 🎓 Key Takeaways

1. **Never store element references** when scraping SPAs
2. **Use Playwright locators** for auto-retrying behavior
3. **URL-based navigation** is more reliable than browser back
4. **Validate page state** before each operation
5. **Implement circuit breakers** to prevent runaway failures
6. **Log metrics** for monitoring and debugging

Choose **Solution 2 (URL-Based)** for the best balance of reliability and simplicity! 🚀
