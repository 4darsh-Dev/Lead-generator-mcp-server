# MCP Server Integration Guide

## Quick Start

### Option 1: Using Python Module (Recommended)

```bash
# From project root
python -m mcp_server.server
```

### Option 2: Using Convenience Script

```bash
python run_mcp_server.py
```

### Option 3: Direct Execution

```bash
python mcp_server/server.py
```

## Claude Desktop Configuration

### Standard Configuration

Edit: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS/Linux)
Or: `%APPDATA%\Claude\claude_desktop_config.json` (Windows)

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

### With Virtual Environment

```json
{
  "mcpServers": {
    "leadgen": {
      "command": "/absolute/path/to/Lead-generator-mcp-server/myenv/bin/python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/absolute/path/to/Lead-generator-mcp-server"
    }
  }
}
```

## Testing

### Manual Test

```bash
# Activate virtual environment
source myenv/bin/activate  # Linux/macOS
# or
myenv\Scripts\activate  # Windows

# Run server
python -m mcp_server.server
```

Server will start and wait for STDIO input. Press Ctrl+C to stop.

### With MCP Inspector

```bash
npm install -g @modelcontextprotocol/inspector
npx @modelcontextprotocol/inspector python -m mcp_server.server
```

## Customization

### Custom Configuration

```python
# custom_server.py
from mcp_server.config import MCPServerConfig
from mcp_server.server import run_server

config = MCPServerConfig(
    name="Custom Lead Server",
    max_scrape_results=1000,
    default_scrape_results=200,
    headless_browser=False
)

run_server(config)
```

### Adding Custom Tools

1. Create tool file: `mcp_server/tools/my_tool.py`

```python
from src.utils.logger import get_logger

logger = get_logger(__name__)

def register_my_tools(mcp):
    @mcp.tool()
    async def my_custom_tool(param: str) -> str:
        """Custom tool description."""
        logger.info(f"Custom tool called with: {param}")
        return f"Result: {param}"
    
    logger.info("Registered custom tools")
```

2. Update `mcp_server/tools/__init__.py`:

```python
from mcp_server.tools.scraping import register_scraping_tools
from mcp_server.tools.my_tool import register_my_tools

__all__ = ["register_scraping_tools", "register_my_tools"]
```

3. Update `mcp_server/server.py`:

```python
from mcp_server.tools import register_scraping_tools, register_my_tools

def create_server(config):
    # ... existing code ...
    register_scraping_tools(mcp)
    register_my_tools(mcp)  # Add this line
    # ... rest of code ...
```

## Architecture

```
Lead-generator-mcp-server/
├── mcp_server/                   # MCP server module (NEW)
│   ├── __init__.py              # Package initialization
│   ├── server.py                # Main server implementation
│   ├── config.py                # Configuration management
│   ├── claude_config.json       # Claude Desktop config template
│   ├── README.md                # Module documentation
│   └── tools/                   # MCP tools (modular)
│       ├── __init__.py          # Tools package
│       └── scraping.py          # Scraping tool implementation
│
├── src/                          # Core application logic
│   ├── core/                    # Scraping logic
│   ├── services/                # Business services
│   ├── utils/                   # Utilities
│   └── mcp-server.py           # DEPRECATED (backward compat)
│
├── run_mcp_server.py            # Convenience runner script
├── mcp.json                     # MCP metadata
└── requirements.txt             # Dependencies
```

## Benefits of Modular Structure

1. **Separation of Concerns**: MCP logic separate from scraping logic
2. **Easy to Extend**: Add new tools without modifying core
3. **Maintainable**: Each component has clear responsibility
4. **Testable**: Mock and test individual components
5. **Configurable**: Centralized configuration management
6. **Reusable**: MCP module can be adapted for other projects

## Troubleshooting

### Import Errors

Ensure PYTHONPATH includes project root:

```bash
export PYTHONPATH=/path/to/Lead-generator-mcp-server:$PYTHONPATH
python -m mcp_server.server
```

Or in Claude config:

```json
{
  "env": {
    "PYTHONPATH": "/path/to/Lead-generator-mcp-server"
  }
}
```

### Server Not Found in Claude

1. Check absolute paths in config
2. Verify Python path: `which python` or `where python`
3. Check logs: `~/Library/Logs/Claude/mcp*.log`
4. Test manually first: `python -m mcp_server.server`

### Module Not Found

Install dependencies:

```bash
pip install -r requirements.txt
playwright install chromium
```

## Migration from Old Structure

If you were using `src/mcp-server.py`:

**Old way:**
```json
{
  "command": "python",
  "args": ["src/mcp-server.py"]
}
```

**New way (recommended):**
```json
{
  "command": "python",
  "args": ["-m", "mcp_server.server"],
  "cwd": "/path/to/Lead-generator-mcp-server"
}
```

The old `src/mcp-server.py` still works but is deprecated.
