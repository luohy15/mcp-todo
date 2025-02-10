from typing import Sequence, Literal
from pydantic import BaseModel

TaskPriority = Literal["low", "medium", "high", "none"]
TaskStatus = Literal["active", "completed", "archived", "all", "none"]

# Task model and related schemas
class Task(BaseModel):
    id: in
    name: str
    desc: str | None = None
    tags: list[str] | None = None
    due_date: str | None = None  # YYYY-MM-DD forma
    priority: TaskPriority | None = None
    status: TaskStatus | None = None
    progress: str | None = None
    created_at: str  # ISO8601 timestamp
    completed_at: str | None = None  # ISO8601 timestamp

class CreateTask(BaseModel):
    name: str
    desc: str | None = None
    tags: list[str] | None = None
    due_date: str | None = None
    priority: TaskPriority | None = None
    status: TaskStatus | None = "active"
    progress: str | None = None

class UpdateTask(BaseModel):
    id: in
    name: str | None = None
    desc: str | None = None
    tags: list[str] | None = None
    due_date: str | None = None
    priority: TaskPriority | None = None
    status: TaskStatus | None = None
    progress: str | None = None

class DeleteTask(BaseModel):
    id: in

class GetTask(BaseModel):
    id: in

class ListTasks(BaseModel):
    keyword: str | None = None
    tags: list[str] | None = None
    priority: TaskPriority | None = None
    status: TaskStatus | None = None
    range: Literal["all", "today", "tomorrow", "day", "week", "month", "quarter", "year"] | None = None
    orderby: Literal["due-date", "priority", "id", "created-at"] = "due-date"  # Default to due-date
    order: Literal["asc", "desc"] = "asc"  # Default to ascending
    limit: int | None = 10  # Default to 10 tasks
