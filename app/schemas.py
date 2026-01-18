from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models import TaskStatus

class TaskCreate(BaseModel):
    task_type: str
    payload: dict

class TaskResponse(BaseModel):
    id: int
    task_type: str
    payload: str
    status: TaskStatus
    result: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class TaskStatusResponse(BaseModel):
    id: int
    status: TaskStatus
    result: Optional[str] = None
    error_message: Optional[str] = None
