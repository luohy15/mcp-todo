# Todo MCP Server

A Model Context Protocol server for managing tasks and todos. This server provides tools to create, read, update, delete and list todo items.

## Tools

1. `task_create`
   - Create a new task
   - Input:
     - `name` (string): Task name
     - `desc` (string, optional): Task description
     - `tags` (string[], optional): Array of tags
     - `due_date` (string, optional): Due date in YYYY-MM-DD format
     - `priority` (string, optional): Task priority (low/medium/high)

2. `task_get`
   - Get a task by ID
   - Input:
     - `id` (number): Task ID

3. `task_update`
   - Update an existing task
   - Input:
     - `id` (number): Task ID
     - `name` (string, optional): New task name
     - `desc` (string, optional): New description
     - `tags` (string[], optional): New tags
     - `due_date` (string, optional): New due date
     - `priority` (string, optional): New priority
     - `status` (string, optional): New status (active/completed/archived)

4. `task_delete`
   - Delete a task
   - Input:
     - `id` (number): Task ID

5. `task_list`
   - List tasks with optional filters
   - Input:
     - `keyword` (string, optional): Search keyword
     - `tags` (string[], optional): Filter by tags
     - `priority` (string, optional): Filter by priority
     - `status` (string, optional): Filter by status

## Configuration

### Environment Variables

- `TODO_FILE_PATH`: Path to the JSONL file for storing tasks. If not set, defaults to "/Users/mac/Nutstore Files/luohy15-data/todo.jsonl"

### Usage with Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "todo": {
      "command": "/path/to/venv/bin/python",
      "args": ["-m", "mcp_server_todo"],
      "env": {
        "TODO_FILE_PATH": "/path/to/your/todo.jsonl"
      }
    }
  }
}
```

## Installation

1. Create a Python virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Unix/macOS
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Development

Run the server directly:
```bash
python -m mcp_server_todo
```

## License

This MCP server is licensed under the MIT License. See the LICENSE file for details.
