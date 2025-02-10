# Todo

A command-line todo application with MCP server capabilities for LLM integration.

## Features

- Command-line interface for managing tasks
- Rich filtering and sorting options
- Support for tags, priorities, and due dates
- MCP server integration for LLM-based task managemen
- JSONL-based storage for easy data manipulation

## Installation

```bash
pip install .
```

## Usage

### CLI Mode

```bash
# Add a new task
todo add "Complete project documentation" -d "Write comprehensive docs" -t "work,docs" -p high -u tomorrow

# List tasks
todo list                    # List all active tasks
todo list -s completed      # List completed tasks
todo list -r today          # List tasks due today
todo list -t work,urgent    # List tasks with specific tags
todo list -p high           # List high priority tasks

# Update a task
todo update 1 -n "New name" -s completed

# Quick complete a task
todo finish 1

# Delete a task
todo delete 1

# Get task details
todo get 1
```

### MCP Server Mode

The package also provides an MCP server for LLM integration:

```bash
todo-mcp
```

This starts the MCP server which provides tools for:
- Creating tasks
- Reading task details
- Updating tasks
- Deleting tasks
- Listing tasks with filters

## Configuration

Configuration file is stored at `~/.config/todo/config.toml`:

```toml
data_file = "~/.local/share/todo/tasks.jsonl"
```

## License

MI
