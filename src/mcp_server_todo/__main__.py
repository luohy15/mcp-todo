import asyncio
import sys
from pathlib import Path

from .cli import main as cli_main
from mcp_server_todo import main

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # If arguments are provided, run in CLI mode
        cli_main()
    else:
        # Otherwise run as MCP server
        main()
