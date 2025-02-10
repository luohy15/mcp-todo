import json
from datetime import datetime, timedelta
from pathlib import Path

from .config import DATA_FILE
from .model import Task, CreateTask, UpdateTask, ListTasks

def load_tasks() -> list[Task]:
    """Load tasks from storage"""
    storage_file = Path(DATA_FILE)
    if not storage_file.exists():
        return []
    tasks = []
    with open(storage_file, "r", encoding="utf-8") as f:
        for line in f:
            task_dict = json.loads(line)
            tasks.append(Task(**task_dict))
    return tasks

def save_tasks(tasks: list[Task]) -> None:
    """Save tasks to storage"""
    storage_file = Path(DATA_FILE)
    # Ensure parent directory exists
    storage_file.parent.mkdir(parents=True, exist_ok=True)
    with open(storage_file, "w", encoding="utf-8") as f:
        for task in tasks:
            f.write(json.dumps(task.model_dump(), ensure_ascii=False) + "\n")

def next_id() -> int:
    """Generate next task ID"""
    tasks = load_tasks()
    return max([t.id for t in tasks], default=0) + 1

def timestamp_iso8601() -> str:
    """Generate ISO8601 timestamp"""
    return datetime.now().isoformat()

# Task operations
def create_task(data: CreateTask) -> Task:
    """Create a new task"""
    task = Task(
        id=next_id(),
        name=data.name,
        desc=data.desc,
        tags=data.tags,
        due_date=data.due_date,
        priority=data.priority,
        status="active",
        progress=data.progress,
        created_at=timestamp_iso8601()
    )
    tasks = load_tasks()
    tasks.append(task)
    save_tasks(tasks)
    return task

def get_task(task_id: int) -> Task | None:
    """Get a task by ID"""
    tasks = load_tasks()
    return next((t for t in tasks if t.id == task_id), None)

def update_task(data: UpdateTask) -> Task:
    """Update an existing task"""
    tasks = load_tasks()
    task = next((t for t in tasks if t.id == data.id), None)
    if not task:
        raise ValueError(f"Task with ID {data.id} not found")

    # Update fields if provided
    if data.name is not None:
        task.name = data.name
    if data.desc is not None:
        task.desc = data.desc
    if data.tags is not None:
        task.tags = data.tags
    if data.due_date is not None:
        task.due_date = data.due_date
    if data.priority is not None:
        task.priority = data.priority
    if data.status is not None:
        old_status = task.status
        task.status = data.status
        if data.status == "completed" and old_status != "completed":
            task.completed_at = timestamp_iso8601()
    if data.progress is not None:
        task.progress = data.progress

    save_tasks(tasks)
    return task

def delete_task(task_id: int) -> bool:
    """Delete a task"""
    tasks = load_tasks()
    filtered_tasks = [t for t in tasks if t.id != task_id]
    if len(filtered_tasks) == len(tasks):
        return False
    save_tasks(filtered_tasks)
    return True

def list_tasks(filters: ListTasks) -> list[Task]:
    """List tasks with optional filters"""
    tasks = load_tasks()

    # Apply basic filters
    status = filters.status or "active"  # Default to active if not specified
    if status != "all":  # Skip status filtering if "all" is specified
        tasks = [t for t in tasks if t.status == status]
    # Convert string "none" to None for priority filter
    priority = None if filters.priority == "none" else filters.priority
    if priority:
        tasks = [t for t in tasks if t.priority == priority]
    if filters.tags:
        tasks = [t for t in tasks if t.tags and any(tag in t.tags for tag in filters.tags)]
    if filters.keyword:
        keyword = filters.keyword.lower()
        tasks = [t for t in tasks if (
            keyword in t.name.lower() or
            (t.desc and keyword in t.desc.lower())
        )]

    # Apply range filter
    if filters.range:
        today = datetime.now().date()
        tasks = [t for t in tasks if t.due_date]  # Filter out tasks without due date

        match filters.range:
            case "today":
                # Tasks due today
                tasks = [t for t in tasks if datetime.strptime(t.due_date, "%Y-%m-%d").date() == today]
            case "tomorrow":
                # Tasks due tomorrow
                tomorrow = today + timedelta(days=1)
                tasks = [t for t in tasks if datetime.strptime(t.due_date, "%Y-%m-%d").date() == tomorrow]
            case "day":
                # Tasks due today (alias for today)
                tasks = [t for t in tasks if datetime.strptime(t.due_date, "%Y-%m-%d").date() == today]
            case "week":
                # Tasks due this week (excluding today)
                week_start = today + timedelta(days=1)  # Start from tomorrow
                week_end = today + timedelta(days=(6 - today.weekday()))  # End on Sunday
                tasks = [t for t in tasks if week_start <= datetime.strptime(t.due_date, "%Y-%m-%d").date() <= week_end]
            case "month":
                # Tasks due this month (excluding this week)
                week_end = today + timedelta(days=(6 - today.weekday()))  # End of current week
                if today.month == 12:
                    month_end = today.replace(day=31)
                else:
                    month_end = (today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                month_start = week_end + timedelta(days=1)  # Start after this week
                tasks = [t for t in tasks if month_start <= datetime.strptime(t.due_date, "%Y-%m-%d").date() <= month_end]
            case "quarter":
                # Tasks due this quarter (excluding this month)
                if today.month == 12:
                    month_end = today.replace(day=31)
                else:
                    month_end = (today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                quarter_month = ((today.month - 1) // 3 + 1) * 3
                if quarter_month == 12:
                    quarter_end = today.replace(month=12, day=31)
                else:
                    quarter_end = (today.replace(month=quarter_month + 1, day=1) - timedelta(days=1))
                quarter_start = month_end + timedelta(days=1)  # Start after this month
                tasks = [t for t in tasks if quarter_start <= datetime.strptime(t.due_date, "%Y-%m-%d").date() <= quarter_end]
            case "year":
                # Tasks due this year (excluding this quarter)
                quarter_month = ((today.month - 1) // 3 + 1) * 3
                if quarter_month == 12:
                    quarter_end = today.replace(month=12, day=31)
                else:
                    quarter_end = (today.replace(month=quarter_month + 1, day=1) - timedelta(days=1))
                year_end = today.replace(month=12, day=31)
                year_start = quarter_end + timedelta(days=1)  # Start after this quarter
                tasks = [t for t in tasks if year_start <= datetime.strptime(t.due_date, "%Y-%m-%d").date() <= year_end]

    # Sort tasks based on orderby parameter
    match filters.orderby:
        case "due-date":
            # Sort by due date, None dates at the end
            tasks.sort(
                key=lambda t: (0, datetime.strptime(t.due_date, "%Y-%m-%d")) if t.due_date else (1, datetime.max),
                reverse=(filters.order == "desc")
            )
        case "priority":
            # Sort by priority (high > medium > low > None)
            priority_order = {"high": 0, "medium": 1, "low": 2}
            tasks.sort(
                key=lambda t: priority_order.get(t.priority, 3),
                reverse=(filters.order == "desc")
            )
        case "id":
            tasks.sort(
                key=lambda t: t.id,
                reverse=(filters.order == "desc")
            )
        case "created-at":
            # Ensure consistent timezone handling by using naive datetimes
            tasks.sort(
                key=lambda t: datetime.fromisoformat(t.created_at).replace(tzinfo=None),
                reverse=(filters.order == "desc")
            )

    limit = filters.limit or 10  # Default to 10 tasks
    return tasks[:limit]  # Apply task limi
