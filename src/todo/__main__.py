import sys
import asyncio

from .cli import main as cli_main
from . import main as mcp_main

def main():
    """Main entry point for the MCP server"""
    if len(sys.argv) > 1:
        # If arguments are provided, run in CLI mode
        cli_main()
    else:
        # Otherwise run as MCP server
        mcp_main()

if __name__ == "__main__":
    main()
