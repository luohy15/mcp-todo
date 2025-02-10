"""Todo - A command-line todo application with MCP server capabilities"""

__version__ = "0.0.1"

import logging
import json
import sys
import platform
from pathlib import Path
from enum import Enum
import click
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .service import (
    create_task,
    get_task,
    update_task,
    delete_task,
    list_tasks
)

from .model import (
    CreateTask,
    GetTask,
    UpdateTask,
    DeleteTask,
    ListTasks
)

class TodoTools(str, Enum):
    CREATE = "task_create"
    READ = "task_get"
    UPDATE = "task_update"
    DELETE = "task_delete"
    LIST = "task_list"

async def serve() -> None:
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    server = Server("mcp-todo")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name=TodoTools.CREATE,
                description="Create a new task",
                inputSchema=CreateTask.schema(),
            ),
            Tool(
                name=TodoTools.READ,
                description="Get a task by ID",
                inputSchema=GetTask.schema(),
            ),
            Tool(
                name=TodoTools.UPDATE,
                description="Update an existing task",
                inputSchema=UpdateTask.schema(),
            ),
            Tool(
                name=TodoTools.DELETE,
                description="Delete a task",
                inputSchema=DeleteTask.schema(),
            ),
            Tool(
                name=TodoTools.LIST,
                description="List tasks with optional filters",
                inputSchema=ListTasks.schema(),
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        try:
            match name:
                case TodoTools.CREATE:
                    task = create_task(CreateTask(**arguments))
                    return [TextContent(
                        type="text",
                        text=f"Task created successfully with ID: {task.id}"
                    )]

                case TodoTools.READ:
                    task = get_task(GetTask(**arguments).id)
                    if not task:
                        return [TextContent(
                            type="text",
                            text="Task not found"
                        )]
                    return [TextContent(
                        type="text",
                        text=json.dumps(task.model_dump(), indent=2, ensure_ascii=False)
                    )]

                case TodoTools.UPDATE:
                    task = update_task(UpdateTask(**arguments))
                    return [TextContent(
                        type="text",
                        text=f"Task {task.id} updated successfully"
                    )]

                case TodoTools.DELETE:
                    success = delete_task(DeleteTask(**arguments).id)
                    return [TextContent(
                        type="text",
                        text="Task deleted successfully" if success else "Task not found"
                    )]

                case TodoTools.LIST:
                    tasks = list_tasks(ListTasks(**arguments))
                    return [TextContent(
                        type="text",
                        text=json.dumps([t.model_dump() for t in tasks], indent=2, ensure_ascii=False)
                    )]

                case _:
                    raise ValueError(f"Unknown tool: {name}")

        except Exception as e:
            logger.error(f"Error processing tool {name}: {str(e)}")
            return [TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]

    options = server.create_initialization_options()
    # Ensure UTF-8 encoding on Windows
    if platform.system() == "Windows":
        import msvcr
        import os
        msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
        msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
        sys.stdin = open(sys.stdin.fileno(), mode='r', encoding='utf-8', buffering=1)
        sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options, raise_exceptions=True)

@click.command()
@click.option("-v", "--verbose", count=True)
def main(verbose: bool) -> None:
    """MCP Todo Server - Todo functionality for MCP"""
    import asyncio

    logging_level = logging.WARN
    if verbose == 1:
        logging_level = logging.INFO
    elif verbose >= 2:
        logging_level = logging.DEBUG

    logging.basicConfig(level=logging_level, stream=sys.stderr)
    asyncio.run(serve())

if __name__ == "__main__":
    main()
