import click
from pathlib import Path
import logging
import sys
from .mcp_server import serve

@click.command()
@click.option("--repository", "-r", type=Path, help="Todo repository path")
@click.option("-v", "--verbose", count=True)
def main(repository: Path | None, verbose: bool) -> None:
    """MCP Todo Server - Todo functionality for MCP"""
    import asyncio

    logging_level = logging.WARN
    if verbose == 1:
        logging_level = logging.INFO
    elif verbose >= 2:
        logging_level = logging.DEBUG

    logging.basicConfig(level=logging_level, stream=sys.stderr)
    asyncio.run(serve(repository))

if __name__ == "__main__":
    main()
