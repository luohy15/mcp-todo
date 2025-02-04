import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Sequence, Literal
from pydantic import BaseModel

from .config import DATA_FILE

# Task model and related schemas
class Task(BaseModel):
    id: int
    name: str
    desc: str | None = None
    tags: list[str] | None = None
    due_date: str | None = None  # YYYY-MM-DD format
    priority: str | None = None  # low/medium/high
    status: str  # active/completed/archived
    created_at: str  # ISO8601 timestamp
    completed_at: str | None = None  # ISO8601 timestamp

class CreateTask(BaseModel):
    name: str
    desc: str | None = None
    tags: list[str] | None = None
    due_date: str | None = None
    priority: str | None = None

class UpdateTask(BaseModel):
    id: int
    name: str | None = None
    desc: str | None = None
    tags: list[str] | None = None
    due_date: str | None = None
    priority: str | None = None
    status: str | None = None

class DeleteTask(BaseModel):
    id: int

class GetTask(BaseModel):
    id: int

class ListTasks(BaseModel):
    keyword: str | None = None
    tags: list[str] | None = None
    priority: str | None = None
    status: str | None = None
    range: Literal["all", "day", "week", "month", "year"] | None = None
    orderby: Literal["due-date", "priority", "id"] = "due-date"  # Default to priority
    limit: int | None = 10  # Default to 10 tasks

def load_tasks() -> list[Task]:
    """Load tasks from storage"""
    storage_file = Path(DATA_FILE)
    if not storage_file.exists():
        return []
    tasks = []
    with open(storage_file, "r") as f:
        for line in f:
            task_dict = json.loads(line)
            tasks.append(Task(**task_dict))
    return tasks

def save_tasks(tasks: list[Task]) -> None:
    """Save tasks to storage"""
    storage_file = Path(DATA_FILE)
    # Ensure parent directory exists
    storage_file.parent.mkdir(parents=True, exist_ok=True)
    with open(storage_file, "w") as f:
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
    tasks = [t for t in tasks if t.status == status]
    if filters.priority:
        tasks = [t for t in tasks if t.priority == filters.priority]
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
            case "day":
                # Tasks due today
                tasks = [t for t in tasks if datetime.strptime(t.due_date, "%Y-%m-%d").date() == today]
            case "week":
                # Tasks due this week (excluding today)
                week_start = today + timedelta(days=1)  # Start from tomorrow
                week_end = today + timedelta(days=7)
                tasks = [t for t in tasks if week_start <= datetime.strptime(t.due_date, "%Y-%m-%d").date() <= week_end]
            case "month":
                # Tasks due this month (excluding this week)
                month_start = today + timedelta(days=8)  # Start after this week
                month_end = (today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)  # Last day of current month
                tasks = [t for t in tasks if month_start <= datetime.strptime(t.due_date, "%Y-%m-%d").date() <= month_end]
            case "year":
                # Tasks due this year (excluding this month)
                year_start = (today.replace(day=1) + timedelta(days=32)).replace(day=1)  # First day of next month
                year_end = today.replace(month=12, day=31)  # Last day of current year
                tasks = [t for t in tasks if year_start <= datetime.strptime(t.due_date, "%Y-%m-%d").date() <= year_end]
    
    # Sort tasks based on orderby parameter
    match filters.orderby:
        case "due-date":
            # Sort by due date, None dates at the end
            tasks.sort(key=lambda t: datetime.strptime(t.due_date, "%Y-%m-%d") if t.due_date else datetime.max)
        case "priority":
            # Sort by priority (high > medium > low > None)
            priority_order = {"high": 0, "medium": 1, "low": 2, None: 3, "none": 3}
            tasks.sort(key=lambda t: priority_order[t.priority])
        case "id":
            tasks.sort(key=lambda t: t.id)

    limit = filters.limit or 10  # Default to 10 tasks
    return tasks[:limit]  # Apply task limit
