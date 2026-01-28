# 🔧 MCP Server Setup & Configuration Guide

## ✅ Changes Made to Follow MCP 2025-11-25 Standards

Your MCP server has been updated to follow the latest Model Context Protocol standards:

### Critical Fixes Applied:

1. **✅ STDIO Transport** (was: HTTP)
   - Changed from `transport="http", port=8080` to `transport="stdio"`
   - STDIO is the **standard transport** for MCP servers
   - Required for Claude Desktop and most MCP clients

2. **✅ Logging to stderr** (was: stdout)
   - All logs now go to `sys.stderr` instead of `sys.stdout`
   - **Critical**: Writing to stdout corrupts JSON-RPC messages in STDIO mode
   - This was breaking the MCP protocol communication

3. **✅ Better Error Handling**
   - Returns structured JSON with error details instead of empty list
   - Provides context about what went wrong
   - Includes input validation for query and max_results

4. **✅ Async Function**
   - Changed tool to `async def` for better compatibility
   - Follows modern Python async patterns

5. **✅ Structured JSON Response**
   - Returns JSON string with `success`, `query`, `results_count`, and `results`
   - More informative than raw list
   - Easier for LLMs to parse

6. **✅ Better Documentation**
   - Added comprehensive docstrings
   - Included usage examples
   - Documented parameter limits

7. **✅ Removed Development Parameters**
   - Removed `reload=True` (development-only feature)
   - Production-ready configuration

---

## 📦 Testing Your MCP Server

### Method 1: Test with Claude Desktop (Recommended)

#### Step 1: Install Claude Desktop
Download from: https://claude.ai/download

#### Step 2: Configure Claude Desktop

**On macOS/Linux:**
```bash
# Create config directory if it doesn't exist
mkdir -p ~/Library/Application\ Support/Claude/

# Edit the configuration file
code ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**On Windows:**
```powershell
# Edit the configuration file
notepad %APPDATA%\Claude\claude_desktop_config.json
```

#### Step 3: Add Your Server Configuration

Add this to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "leadgen": {
      "command": "python",
      "args": [
        "/ABSOLUTE/PATH/TO/Lead-generator-mcp-server/src/mcp-server.py"
      ],
      "env": {
        "PYTHONPATH": "/ABSOLUTE/PATH/TO/Lead-generator-mcp-server"
      }
    }
  }
}
```

**Important Notes:**
- Replace `/ABSOLUTE/PATH/TO/` with your actual path
- On macOS/Linux: Get path with `pwd` command
- On Windows: Use double backslashes: `C:\\Users\\...` or forward slashes: `C:/Users/...`
- If using a virtual environment, use the full path to Python in venv:
  ```json
  "command": "/ABSOLUTE/PATH/TO/Lead-generator-mcp-server/myenv/bin/python"
  ```

#### Step 4: Restart Claude Desktop

After saving the config, completely quit and restart Claude Desktop.

#### Step 5: Test the Connection

In Claude Desktop, look for the "📎" icon at the bottom. Click it and you should see:
- **Connectors** → `leadgen` server with `scrape_google_maps` tool

Try asking Claude:
```
"Can you scrape coffee shops in Seattle using the leadgen connector?"
```

---

### Method 2: Test with MCP Inspector (Development)

The MCP Inspector is a debugging tool:

```bash
# Install MCP Inspector
npm install -g @modelcontextprotocol/inspector

# Run your server with inspector
npx @modelcontextprotocol/inspector python src/mcp-server.py
```

This opens a web interface where you can test your tools directly.

---

## 🔍 Troubleshooting

### Server Not Showing in Claude Desktop

1. **Check logs location (macOS/Linux):**
   ```bash
   tail -f ~/Library/Logs/Claude/mcp*.log
   ```

2. **Check logs location (Windows):**
   ```powershell
   Get-Content $env:APPDATA\Claude\logs\mcp*.log -Wait
   ```

3. **Common issues:**
   - ❌ Incorrect absolute path in config
   - ❌ Python not in PATH or wrong Python version
   - ❌ Missing dependencies (run `pip install -r requirements.txt`)
   - ❌ Playwright browsers not installed (run `playwright install chromium`)
   - ❌ JSON syntax error in config file

### Test Server Manually

```bash
# Activate your virtual environment
source myenv/bin/activate  # On Linux/macOS
# or
myenv\Scripts\activate  # On Windows

# Run the server
cd src
python mcp-server.py
```

The server should start and wait for STDIO input. Press `Ctrl+C` to stop.

### Verify Python Path

```bash
# Show full path to Python
which python  # On Linux/macOS
where python  # On Windows
```

Use this full path in your Claude Desktop config.

---

## 📋 MCP Standards Compliance Checklist

Your server now complies with:

- ✅ **MCP Specification 2025-11-25**
- ✅ **STDIO Transport** (standard for desktop clients)
- ✅ **stderr logging** (prevents JSON-RPC corruption)
- ✅ **Proper error handling** with structured responses
- ✅ **Type hints** and comprehensive documentation
- ✅ **Async/await** patterns
- ✅ **Dependency declaration** (`playwright`)
- ✅ **Input validation**
- ✅ **JSON response format**

### Optional Enhancements (Future)

Consider adding these MCP features:

1. **Resources**: Expose scraped data as readable resources
   ```python
   @mcp.resource("leads://recent")
   async def get_recent_leads():
       """Get recently scraped leads"""
       # Return cached or stored leads
   ```

2. **Prompts**: Pre-built prompt templates
   ```python
   @mcp.prompt()
   async def analyze_leads(industry: str):
       """Generate prompt for lead analysis"""
       return f"Analyze these {industry} leads..."
   ```

3. **SSE/HTTP Transport**: For web-based clients
   ```python
   # For web clients, you can use SSE transport
   mcp.run(transport="sse")
   ```

4. **Progress Updates**: Long-running scraping with progress
   ```python
   # Send progress notifications during scraping
   async def scrape_with_progress(query, max_results):
       # Use MCP progress notifications
   ```

---

## 🚀 Next Steps

1. ✅ Server is now MCP-compliant
2. 📝 Update your README.md with new STDIO instructions
3. 🧪 Test with Claude Desktop
4. 📊 Consider adding Resources/Prompts for richer functionality
5. 🔒 Add authentication if exposing remotely (OAuth/API keys)

---

## 📚 Additional Resources

- [MCP Official Docs](https://modelcontextprotocol.io/)
- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [FastMCP Documentation](https://gofastmcp.com/)
- [Claude Desktop MCP Guide](https://modelcontextprotocol.io/quickstart)
- [MCP Inspector Tool](https://github.com/modelcontextprotocol/inspector)

---

## ❓ Questions?

If you encounter issues:
1. Check the troubleshooting section above
2. Review Claude Desktop logs
3. Test server manually with `python mcp-server.py`
4. Verify all dependencies are installed
5. Ensure Playwright browsers are installed: `playwright install chromium`

Your server is now production-ready and follows all MCP best practices! 🎉
