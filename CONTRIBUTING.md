# Contributing to Lead Generator MCP Server

Thank you for your interest in contributing! 🎉

## 📋 Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community

## 🚀 Getting Started

### 1. Fork & Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/Lead-generator-mcp-server.git
cd Lead-generator-mcp-server
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv myenv
source myenv/bin/activate  # Windows: myenv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

## 🐛 Reporting Bugs

When reporting bugs, include:

- Python version (`python --version`)
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages/screenshots
- Query used (if applicable)

## 💡 Suggesting Features

Feature requests should include:

- Clear use case
- Expected behavior
- Why it would be useful
- Possible implementation approach

## 📝 Code Contribution Guidelines

### Code Style

- Follow PEP 8 style guide
- Use type hints where possible
- Add docstrings to functions/classes
- Keep functions focused and small

### Example:

```python
def extract_business_data(self, max_results: int = 100) -> List[Dict]:
    """
    Extract data from business listings.
    
    Args:
        max_results: Maximum number of businesses to extract
        
    Returns:
        List of dictionaries containing business data
    """
    # Implementation...
```

### Testing

- Test your changes manually
- Run with `--visible` flag to debug
- Try different queries and locations
- Check error handling

### Commit Messages

Use clear, descriptive commit messages:

```bash
# Good
git commit -m "Add phone number validation for international formats"
git commit -m "Fix scrolling issue on slow connections"

# Bad
git commit -m "Update code"
git commit -m "Fix bug"
```

## 🔄 Pull Request Process

1. **Update documentation** if needed
2. **Add comments** to complex code
3. **Test thoroughly** before submitting
4. **Update README.md** if adding features
5. **Fill out PR template** completely

### PR Title Format

```
[Type] Brief description

Types: Feature, Bugfix, Docs, Refactor, Performance
```

Examples:
- `[Feature] Add support for multiple search queries`
- `[Bugfix] Fix timeout error in scroll_results()`
- `[Docs] Update installation instructions`

## 🏗️ Architecture Guidelines

### Adding New Features

When adding features, consider:

- **Performance**: Don't slow down scraping
- **Error Handling**: Add try/except blocks
- **Logging**: Use `logger.info/warning/error`
- **Anti-Detection**: Maintain human-like behavior

### Code Organization

```
src/
├── scraper.py      # Core scraping logic
├── mcp-server.py   # MCP server wrapper
└── utils.py        # Helper functions (if needed)
```

## 🎯 Areas We Need Help

- [ ] Add support for more search filters
- [ ] Implement proxy support
- [ ] Add unit tests
- [ ] Improve lead scoring algorithm
- [ ] Add more data validation
- [ ] Create Docker image
- [ ] Add CI/CD pipeline
- [ ] Improve documentation
- [ ] Add more export formats (JSON, Excel)
- [ ] Implement caching mechanism

## 📚 Resources

- [Playwright Documentation](https://playwright.dev/python/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Google Maps](https://www.google.com/maps)
- [PEP 8 Style Guide](https://pep8.org/)

## ❓ Questions?

- Open a [GitHub Issue](https://github.com/4darsh-Dev/Lead-generator-mcp-server/issues)
- Check existing issues/PRs first

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing! 🙏
