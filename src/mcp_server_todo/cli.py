import argparse
import json
import sys
from datetime import datetime
from typing import Any, NoReturn, Sequence

from tabulate import tabulate
import wcwidth

from .service import (
    create_task,
    get_task,
    update_task,
    delete_task,
    list_tasks,
    CreateTask,
    UpdateTask,
    ListTasks,
)

def format_task_for_table(task: dict[str, Any]) -> list[Any]:
    """Format task data for tabulate table row"""
    # Format dates
    created_at = datetime.fromisoformat(task['created_at']).strftime('%Y-%m-%d %H:%M') if task.get('created_at') else ''
    completed_at = datetime.fromisoformat(task['completed_at']).strftime('%Y-%m-%d %H:%M') if task.get('completed_at') else ''
    due_date = task.get('due_date', '')
    
    # Format tags
    tags = ', '.join(task.get('tags', [])) if task.get('tags') else ''
    
    return [
        task['id'],
        task['name'],
        task['desc'] or '',
        task['status'],
        task.get('priority', ''),
        tags,
        due_date,
        created_at,
        completed_at
    ]

def format_tasks_table(tasks: Sequence[dict[str, Any]]) -> str:
    """Format multiple tasks as a table using tabulate"""
    if not tasks:
        return "No tasks found"
    
    headers = ['ID', 'Name', 'Description', 'Status', 'Priority', 'Tags', 'Due Date', 'Created', 'Completed']
    rows = [format_task_for_table(task) for task in tasks]
    
    return tabulate(
        rows,
        headers=headers,
        tablefmt='simple',
        maxcolwidths=[6, 20, 30, 15, 10, 15, 15, 15, 15],
        numalign='left',
        stralign='left'
    )

def format_task_output(task_data: dict[str, Any]) -> str:
    """Format task data for terminal output"""
    # Format dates for better readability
    for field in ['created_at', 'completed_at']:
        if task_data.get(field):
            dt = datetime.fromisoformat(task_data[field])
            task_data[field] = dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Format tags list
    if task_data.get('tags'):
        task_data['tags'] = ', '.join(task_data['tags'])
    
    # Create formatted output
    lines = [
        f"ID: {task_data['id']}",
        f"Name: {task_data['name']}",
        f"Status: {task_data['status']}",
    ]
    
    # Add optional fields if present
    if task_data.get('desc'):
        lines.append(f"Description: {task_data['desc']}")
    if task_data.get('tags'):
        lines.append(f"Tags: {task_data['tags']}")
    if task_data.get('due_date'):
        lines.append(f"Due Date: {task_data['due_date']}")
    if task_data.get('priority'):
        lines.append(f"Priority: {task_data['priority']}")
    if task_data.get('created_at'):
        lines.append(f"Created: {task_data['created_at']}")
    if task_data.get('completed_at'):
        lines.append(f"Completed: {task_data['completed_at']}")
    
    return '\n'.join(lines)

def parse_tags(tags_str: str | None) -> list[str] | None:
    """Parse comma-separated tags string into list"""
    if not tags_str:
        return None
    return [tag.strip() for tag in tags_str.split(',') if tag.strip()]

def cmd_add(args: argparse.Namespace) -> None:
    """Handle 'add' command"""
    task = create_task(CreateTask(
        name=args.name,
        desc=args.desc,
        tags=parse_tags(args.tags),
        due_date=args.due,
        priority=args.priority
    ))
    print(f"Task created successfully with ID: {task.id}")
    print("\nTask details:")
    print(format_task_output(task.model_dump()))

def cmd_get(args: argparse.Namespace) -> None:
    """Handle 'get' command"""
    task = get_task(args.id)
    if not task:
        print(f"Task with ID {args.id} not found")
        sys.exit(1)
    print(format_task_output(task.model_dump()))

def cmd_update(args: argparse.Namespace) -> None:
    """Handle 'update' command"""
    update_data = {'id': args.id}
    
    # Only include provided fields
    if args.name is not None:
        update_data['name'] = args.name
    if args.desc is not None:
        update_data['desc'] = args.desc
    if args.tags is not None:
        update_data['tags'] = parse_tags(args.tags)
    if args.due is not None:
        update_data['due_date'] = args.due
    if args.priority is not None:
        update_data['priority'] = args.priority
    if args.status is not None:
        update_data['status'] = args.status
    
    try:
        task = update_task(UpdateTask(**update_data))
        print(f"Task {task.id} updated successfully")
        print("\nUpdated task details:")
        print(format_task_output(task.model_dump()))
    except ValueError as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

def cmd_delete(args: argparse.Namespace) -> None:
    """Handle 'delete' command"""
    if delete_task(args.id):
        print(f"Task {args.id} deleted successfully")
    else:
        print(f"Task with ID {args.id} not found")
        sys.exit(1)

def cmd_list(args: argparse.Namespace) -> None:
    """Handle 'list' command"""
    tasks = list_tasks(ListTasks(
        keyword=args.keyword,
        tags=parse_tags(args.tags),
        priority=args.priority,
        status=args.status,
        range=args.range,
        orderby=args.orderby,
        limit=args.limit
    ))
    
    if tasks:
        print(f"Found {len(tasks)} tasks:\n")
        print(format_tasks_table([task.model_dump() for task in tasks]))
    else:
        print("No tasks found")

def main() -> NoReturn:
    parser = argparse.ArgumentParser(description="Todo CLI")
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add a new task')
    add_parser.add_argument('name', help='Task name')
    add_parser.add_argument('--desc', help='Task description')
    add_parser.add_argument('--tags', help='Comma-separated tags')
    add_parser.add_argument('--due', help='Due date (YYYY-MM-DD)')
    add_parser.add_argument('--priority', choices=['low', 'medium', 'high'], help='Task priority')
    
    # Get command
    get_parser = subparsers.add_parser('get', help='Get task details')
    get_parser.add_argument('id', type=int, help='Task ID')
    
    # Update command
    update_parser = subparsers.add_parser('update', help='Update a task')
    update_parser.add_argument('id', type=int, help='Task ID')
    update_parser.add_argument('--name', help='New task name')
    update_parser.add_argument('--desc', help='New task description')
    update_parser.add_argument('--tags', help='New comma-separated tags')
    update_parser.add_argument('--due', help='New due date (YYYY-MM-DD)')
    update_parser.add_argument('--priority', choices=['low', 'medium', 'high'], help='New task priority')
    update_parser.add_argument('--status', choices=['active', 'completed', 'archived'], help='New task status')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a task')
    delete_parser.add_argument('id', type=int, help='Task ID')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List tasks')
    list_parser.add_argument('--keyword', help='Search keyword')
    list_parser.add_argument('--tags', help='Filter by comma-separated tags')
    list_parser.add_argument('--priority', choices=['low', 'medium', 'high'], help='Filter by priority')
    list_parser.add_argument('--status', choices=['active', 'completed', 'archived'], help='Filter by status')
    list_parser.add_argument('--range', choices=['all', 'day', 'week', 'month', 'year'], help='Filter by due date range')
    list_parser.add_argument('--orderby', choices=['due-date', 'priority', 'id'], default='due-date', help='Sort tasks by field')
    list_parser.add_argument('--limit', type=int, help='Maximum number of tasks to display (default: 10)')
    
    args = parser.parse_args()
    
    try:
        match args.command:
            case 'add':
                cmd_add(args)
            case 'get':
                cmd_get(args)
            case 'update':
                cmd_update(args)
            case 'delete':
                cmd_delete(args)
            case 'list':
                cmd_list(args)
            case _:
                parser.print_help()
                sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
