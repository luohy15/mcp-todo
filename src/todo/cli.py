import sys
from datetime import datetime, timedelta
from typing import Any, Optional, Sequence

import click
from tabulate import tabulate

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
    
    # Format tags
    tags = ', '.join(task.get('tags', [])) if task.get('tags') else ''
    
    return [
        task['id'],
        task['name'],
        task.get('desc') or '',
        task['status'],
        task.get('priority') or '',
        tags,
        task.get('due_date') or '',
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

def get_end_of_week(dt: datetime) -> datetime:
    """Get the end of the week (Sunday) for a given date"""
    # days_ahead is 6 for Sunday, 5 for Monday, etc.
    days_ahead = 6 - dt.weekday()
    return dt.replace(hour=23, minute=59, second=59) + timedelta(days=days_ahead)

def get_end_of_quarter(dt: datetime) -> datetime:
    """Get the end of the current quarter for a given date"""
    # Determine which quarter we're in and return the corresponding end date
    quarter_month = ((dt.month - 1) // 3 + 1) * 3
    # Create date for last day of quarter
    if quarter_month == 12:
        return datetime(dt.year, 12, 31, 23, 59, 59)
    else:
        # Use first day of next month - 1 day to get last day of current month
        next_month = datetime(dt.year, quarter_month + 1, 1, 23, 59, 59)
        return next_month - timedelta(days=1)

def get_end_of_year(dt: datetime) -> datetime:
    """Get the end of the year for a given date"""
    return datetime(dt.year, 12, 31, 23, 59, 59)

def parse_due_date(due: str | None) -> str | None:
    """Parse due date string, supporting both YYYY-MM-DD format and shortcuts"""
    if not due:
        return None
        
    due = due.lower()
    today = datetime.now()
    
    match due:
        case 'today':
            return today.strftime('%Y-%m-%d')
        case 'tomorrow':
            return (today + timedelta(days=1)).strftime('%Y-%m-%d')
        case 'week':
            # End of current week (Sunday)
            return get_end_of_week(today).strftime('%Y-%m-%d')
        case 'month':
            # End of current month
            if today.month == 12:
                next_month = datetime(today.year + 1, 1, 1)
            else:
                next_month = datetime(today.year, today.month + 1, 1)
            end_of_month = next_month - timedelta(days=1)
            return end_of_month.strftime('%Y-%m-%d')
        case 'quarter':
            # End of current quarter
            return get_end_of_quarter(today).strftime('%Y-%m-%d')
        case 'year':
            # End of current year
            return get_end_of_year(today).strftime('%Y-%m-%d')
        case _:
            # Assume it's in YYYY-MM-DD format
            try:
                # Validate the date format
                datetime.strptime(due, '%Y-%m-%d')
                return due
            except ValueError:
                raise click.BadParameter(
                    'Due date must be YYYY-MM-DD or one of: today, tomorrow, week, month, quarter, year'
                )

@click.group()
def cli():
    """Todo CLI - Manage your tasks efficiently"""
    pass

@cli.command()
@click.argument('name')
@click.option('-d', '--desc', help='Task description')
@click.option('-t', '--tags', help='Comma-separated tags')
@click.option('-u', '--due', help='Due date (YYYY-MM-DD or today/tomorrow/week=Sunday/month=end-of-month/quarter=end-of-quarter/year=end-of-year)')
@click.option('-p', '--priority', type=click.Choice(['low', 'medium', 'high']), help='Task priority')
def add(name: str, desc: Optional[str], tags: Optional[str], due: Optional[str], priority: Optional[str]):
    """Add a new task"""
    task = create_task(CreateTask(
        name=name,
        desc=desc,
        tags=parse_tags(tags),
        due_date=parse_due_date(due),
        priority=priority
    ))
    click.echo(f"Task created successfully with ID: {task.id}")
    click.echo("\nTask details:")
    click.echo(format_task_output(task.model_dump()))

@cli.command()
@click.argument('id', type=int)
def get(id: int):
    """Get task details"""
    task = get_task(id)
    if not task:
        click.echo(f"Task with ID {id} not found", err=True)
        sys.exit(1)
    click.echo(format_task_output(task.model_dump()))

@cli.command()
@click.argument('id', type=int)
@click.option('-n', '--name', help='New task name')
@click.option('-d', '--desc', help='New task description')
@click.option('-t', '--tags', help='New comma-separated tags')
@click.option('-u', '--due', help='New due date (YYYY-MM-DD or today/tomorrow/week=Sunday/month=end-of-month/quarter=end-of-quarter/year=end-of-year)')
@click.option('-p', '--priority', type=click.Choice(['low', 'medium', 'high']), help='New task priority')
@click.option('-s', '--status', type=click.Choice(['active', 'completed', 'archived']), help='New task status')
def update(id: int, name: Optional[str], desc: Optional[str], tags: Optional[str], 
          due: Optional[str], priority: Optional[str], status: Optional[str]):
    """Update a task"""
    update_data = {'id': id}
    
    # Only include provided fields
    if name is not None:
        update_data['name'] = name
    if desc is not None:
        update_data['desc'] = desc
    if tags is not None:
        update_data['tags'] = parse_tags(tags)
    if due is not None:
        update_data['due_date'] = parse_due_date(due)
    if priority is not None:
        update_data['priority'] = priority
    if status is not None:
        update_data['status'] = status
    
    try:
        task = update_task(UpdateTask(**update_data))
        click.echo(f"Task {task.id} updated successfully")
        click.echo("\nUpdated task details:")
        click.echo(format_task_output(task.model_dump()))
    except ValueError as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('id', type=int)
def finish(id: int):
    """Mark a task as completed (shortcut for: update --status completed)"""
    try:
        task = update_task(UpdateTask(id=id, status='completed'))
        click.echo(f"Task {task.id} marked as completed")
        click.echo("\nUpdated task details:")
        click.echo(format_task_output(task.model_dump()))
    except ValueError as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('id', type=int)
def delete(id: int):
    """Delete a task"""
    if delete_task(id):
        click.echo(f"Task {id} deleted successfully")
    else:
        click.echo(f"Task with ID {id} not found", err=True)
        sys.exit(1)

@cli.command()
@click.option('-k', '--keyword', help='Search keyword')
@click.option('-t', '--tags', help='Filter by comma-separated tags')
@click.option('-p', '--priority', type=click.Choice(['low', 'medium', 'high']), help='Filter by priority')
@click.option('-s', '--status', type=click.Choice(['active', 'completed', 'archived']), help='Filter by status')
@click.option('-r', '--range', type=click.Choice(['all', 'today', 'tomorrow', 'day', 'week', 'month', 'quarter', 'year']), 
          help='Filter by due date range (today=due today/tomorrow=due tomorrow/week=due after today until Sunday/'
               'month=due after this week until month end/quarter=due after this month until quarter end/'
               'year=due after this quarter until year end)')
@click.option('-o', '--orderby', type=click.Choice(['due-date', 'priority', 'id', 'created-at']), default='due-date', help='Sort tasks by field')
@click.option('-d', '--order', type=click.Choice(['asc', 'desc']), default='asc', help='Sort order (ascending/descending)')
@click.option('-l', '--limit', type=int, help='Maximum number of tasks to display (default: 10)')
def list(keyword: Optional[str], tags: Optional[str], priority: Optional[str], 
         status: Optional[str], range: Optional[str], orderby: str, order: str, limit: Optional[int]):
    """List tasks with optional filters"""
    tasks = list_tasks(ListTasks(
        keyword=keyword,
        tags=parse_tags(tags),
        priority=priority,
        status=status,
        range=range,
        orderby=orderby,
        order=order,
        limit=limit
    ))
    
    if tasks:
        click.echo(f"Found {len(tasks)} tasks:\n")
        click.echo(format_tasks_table([task.model_dump() for task in tasks]))
    else:
        click.echo("No tasks found")

def main():
    cli()

if __name__ == '__main__':
    main()
