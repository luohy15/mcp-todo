from typing import Sequence, Literal
from pydantic import BaseModel

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
    range: Literal["all", "today", "tomorrow", "day", "week", "month", "quarter", "year"] | None = None
    orderby: Literal["due-date", "priority", "id", "created-at"] = "due-date"  # Default to priority
    order: Literal["asc", "desc"] = "asc"  # Default to ascending
    limit: int | None = 10  # Default to 10 tasks
