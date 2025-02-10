import sys
import shutil
from datetime import datetime, timedelta
from typing import Any, Optional, Sequence

import click
from tabulate import tabulate

def get_column_widths(total_width: int) -> list[int]:
    """Calculate column widths based on terminal width and content ratios"""
    # Reserve some space for table borders and padding
    available_width = max(total_width - 20, 80)  # minimum 80 chars, account for borders
    
    # Define column ratios (total 100)
    ratios = {
        'id': 5,        # ID column (smallest)
        'name': 20,     # Name (largest)
        'desc': 15,     # Description
        'status': 10,   # Status
        'progress': 10, # Progress
        'due': 10,      # Due date
        'priority': 5,  # Priority
        'tags': 5,      # Tags
        'created': 10,  # Created date
        'completed': 10 # Completed date
    }
    
    # Calculate width for each column
    widths = []
    for ratio in ratios.values():
        # Calculate width and ensure minimum of 3 characters
        width = max(int((ratio / 100) * available_width), 3)
        widths.append(width)
    
    return widths

from .service import (
    create_task,
    get_task,
    update_task,
    delete_task,
    list_tasks
)

from .model import (
    CreateTask,
    UpdateTask,
    ListTasks
)

def truncate_text(text: str, max_length: int) -> str:
    """Truncate text to max_length with ellipsis if needed"""
    if not text or len(text) <= max_length:
        return text
    return text[:max_length-3] + '...'

def format_task_for_table(task: dict[str, Any]) -> list[Any]:
    """Format task data for tabulate table row"""
    # Get terminal width and calculate column widths
    terminal_width = shutil.get_terminal_size().columns
    widths = get_column_widths(terminal_width)
    
    # Format dates
    created_at = datetime.fromisoformat(task['created_at']).strftime('%Y-%m-%d %H:%M') if task.get('created_at') else ''
    completed_at = datetime.fromisoformat(task['completed_at']).strftime('%Y-%m-%d %H:%M') if task.get('completed_at') else ''
    
    # Format tags
    tags = ', '.join(task.get('tags', [])) if task.get('tags') else ''
    
    # Return formatted data with truncation where appropriate
    return [
        task['id'],  # ID is numeric, no truncation needed
        truncate_text(task['name'], widths[1]),
        truncate_text(task.get('desc') or '', widths[2]),
        task['status'],  # Status is enum, no truncation needed
        truncate_text(task.get('progress') or '', widths[4]),
        task.get('due_date') or '',  # Date format is fixed, no truncation needed
        task.get('priority') or '',  # Priority is enum, no truncation needed
        truncate_text(tags, widths[7]),
        created_at,  # Date format is fixed, no truncation needed
        completed_at  # Date format is fixed, no truncation needed
    ]

def format_tasks_table(tasks: Sequence[dict[str, Any]]) -> str:
    """Format multiple tasks as a table using tabulate"""
    if not tasks:
        return "No tasks found"
    
    headers = ['ID', 'Name', 'Description', 'Status', 'Progress', 'Due Date', 'Priority', 'Tags', 'Created', 'Completed']
    rows = [format_task_for_table(task) for task in tasks]
    
    # Get terminal width
    terminal_width = shutil.get_terminal_size().columns
    
    # Calculate dynamic column widths
    column_widths = get_column_widths(terminal_width)
    
    return tabulate(
        rows,
        headers=headers,
        tablefmt='simple',
        maxcolwidths=column_widths,
        numalign='left',
        stralign='left'
    )

def parse_task_ids(ids_str: str) -> list[int]:
    """Parse comma-separated task IDs string into list of integers"""
    try:
        return [int(id.strip()) for id in ids_str.split(',') if id.strip()]
    except ValueError:
        raise click.BadParameter('Task IDs must be comma-separated integers')

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
@click.option('-g', '--progress', help='Task progress')
def add(name: str, desc: Optional[str], tags: Optional[str], due: Optional[str], priority: Optional[str], progress: Optional[str]):
    """Add a new task"""
    task = create_task(CreateTask(
        name=name,
        desc=desc,
        tags=parse_tags(tags),
        due_date=parse_due_date(due),
        priority=priority,
        progress=progress
    ))
    click.echo(f"Task created successfully with ID: {task.id}")
    click.echo("\nTask details:")
    click.echo(format_tasks_table([task.model_dump()]))

@cli.command()
@click.argument('ids')
def get(ids: str):
    """Get details for one or more tasks (comma-separated IDs)"""
    task_ids = parse_task_ids(ids)
    successes = []
    failures = []
    
    for task_id in task_ids:
        task = get_task(task_id)
        if task:
            successes.append(task)
        else:
            failures.append((task_id, "Task not found"))
    
    if successes:
        click.echo(f"Found {len(successes)} task(s):\n")
        click.echo(format_tasks_table([task.model_dump() for task in successes]))
    
    if failures:
        click.echo("\nFailed to get the following tasks:", err=True)
        for task_id, error in failures:
            click.echo(f"Task {task_id}: {error}", err=True)
        
    if failures and not successes:
        sys.exit(1)

@cli.command()
@click.argument('ids')
@click.option('-n', '--name', help='New task name')
@click.option('-d', '--desc', help='New task description')
@click.option('-t', '--tags', help='New comma-separated tags')
@click.option('-u', '--due', help='New due date (YYYY-MM-DD or today/tomorrow/week=Sunday/month=end-of-month/quarter=end-of-quarter/year=end-of-year)')
@click.option('-p', '--priority', type=click.Choice(['low', 'medium', 'high']), help='New task priority')
@click.option('-s', '--status', type=click.Choice(['active', 'completed', 'archived']), help='New task status')
@click.option('-g', '--progress', help='New task progress')
def update(ids: str, name: Optional[str], desc: Optional[str], tags: Optional[str], 
          due: Optional[str], priority: Optional[str], status: Optional[str], progress: Optional[str]):
    """Update one or more tasks (comma-separated IDs)"""
    task_ids = parse_task_ids(ids)
    successes = []
    failures = []
    
    base_update_data = {}
    # Only include provided fields
    if name is not None:
        base_update_data['name'] = name
    if desc is not None:
        base_update_data['desc'] = desc
    if tags is not None:
        base_update_data['tags'] = parse_tags(tags)
    if due is not None:
        base_update_data['due_date'] = parse_due_date(due)
    if priority is not None:
        base_update_data['priority'] = priority
    if status is not None:
        base_update_data['status'] = status
    if progress is not None:
        base_update_data['progress'] = progress
    
    for task_id in task_ids:
        try:
            update_data = {'id': task_id, **base_update_data}
            task = update_task(UpdateTask(**update_data))
            successes.append(task)
        except ValueError as e:
            failures.append((task_id, str(e)))
    
    # Print results
    if successes:
        click.echo(f"Successfully updated {len(successes)} task(s):")
        click.echo(format_tasks_table([task.model_dump() for task in successes]))
    
    if failures:
        click.echo("\nFailed to update the following tasks:", err=True)
        for task_id, error in failures:
            click.echo(f"Task {task_id}: {error}", err=True)
        
    if failures and not successes:
        sys.exit(1)

@cli.command()
@click.argument('ids')
def finish(ids: str):
    """Mark one or more tasks as completed (shortcut for: update --status completed)"""
    task_ids = parse_task_ids(ids)
    successes = []
    failures = []
    
    for task_id in task_ids:
        try:
            task = update_task(UpdateTask(id=task_id, status='completed'))
            successes.append(task)
        except ValueError as e:
            failures.append((task_id, str(e)))
    
    if successes:
        click.echo(f"Successfully completed {len(successes)} task(s):")
        click.echo(format_tasks_table([task.model_dump() for task in successes]))
    
    if failures:
        click.echo("\nFailed to complete the following tasks:", err=True)
        for task_id, error in failures:
            click.echo(f"Task {task_id}: {error}", err=True)
        
    if failures and not successes:
        sys.exit(1)

@cli.command()
@click.argument('ids')
def delete(ids: str):
    """Delete one or more tasks (comma-separated IDs)"""
    task_ids = parse_task_ids(ids)
    successes = []
    failures = []
    
    for task_id in task_ids:
        if delete_task(task_id):
            successes.append(task_id)
        else:
            failures.append((task_id, "Task not found"))
    
    if successes:
        click.echo(f"Successfully deleted {len(successes)} task(s): {', '.join(map(str, successes))}")
    
    if failures:
        click.echo("\nFailed to delete the following tasks:", err=True)
        for task_id, error in failures:
            click.echo(f"Task {task_id}: {error}", err=True)
        
    if failures and not successes:
        sys.exit(1)

@cli.command()
@click.option('-k', '--keyword', help='Search keyword')
@click.option('-t', '--tags', help='Filter by comma-separated tags')
@click.option('-p', '--priority', type=click.Choice(['low', 'medium', 'high']), help='Filter by priority')
@click.option('-s', '--status', type=click.Choice(['all', 'active', 'completed', 'archived']), help='Filter by status (default: active)')
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
