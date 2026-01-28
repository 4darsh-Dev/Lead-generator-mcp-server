# MCP Server Module

Model Context Protocol server implementation for Lead Generation.

## Structure

```
mcp_server/
├── __init__.py          # Package initialization
├── server.py            # Main server implementation
├── config.py            # Configuration management
├── README.md            # This file
└── tools/               # MCP tools (modular)
    ├── __init__.py      # Tools package init
    └── scraping.py      # Google Maps scraping tool
```

## Quick Start

### Run the Server

```bash
# From project root
python -m mcp_server.server

# Or using convenience script
python run_mcp_server.py

# Or directly
python mcp_server/server.py
```

### Use with Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "leadgen": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/absolute/path/to/Lead-generator-mcp-server"
    }
  }
}
```

## Configuration

Edit `mcp_server/config.py` to customize:

```python
from mcp_server.config import MCPServerConfig

config = MCPServerConfig(
    name="Custom Server Name",
    max_scrape_results=1000,
    headless_browser=False
)
```

## Adding New Tools

1. Create a new tool module in `mcp_server/tools/`:

```python
# mcp_server/tools/my_tool.py
def register_my_tools(mcp):
    @mcp.tool()
    async def my_tool(param: str) -> str:
        """Tool description."""
        return "result"
```

2. Register in `mcp_server/tools/__init__.py`:

```python
from mcp_server.tools.my_tool import register_my_tools

__all__ = ["register_scraping_tools", "register_my_tools"]
```

3. Register in `mcp_server/server.py`:

```python
from mcp_server.tools import register_my_tools

def create_server(config):
    # ... existing code ...
    register_my_tools(mcp)
    # ... rest of code ...
```

## Standards Compliance

- ✅ MCP Specification 2025-11-25
- ✅ STDIO transport (default)
- ✅ stderr logging (prevents JSON-RPC corruption)
- ✅ Modular tool architecture
- ✅ Configurable settings
- ✅ Comprehensive error handling

## Available Tools

### scrape_google_maps

Scrapes business data from Google Maps.

**Parameters:**
- `query` (str): Search query (e.g., "coffee shops in Seattle")
- `max_results` (int, optional): Max results to scrape (default: 100, max: 500)

**Returns:**
- JSON string with success status, results count, and business data

**Example:**
```python
result = await scrape_google_maps("restaurants in NYC", 50)
```
