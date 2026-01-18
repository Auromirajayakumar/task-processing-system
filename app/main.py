import time
from fastapi import Request
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
import json
from datetime import datetime, timedelta

from app.database import get_db, init_db
from app.models import Task, TaskStatus
from app.schemas import TaskCreate, TaskResponse, TaskStatusResponse
from app.worker import WorkerPool

app = FastAPI(title="Task Processing System", version="1.0.0")

# Global worker pool instance
worker_pool = None

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add response time tracking"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.on_event("startup")
async def startup_event():
    """Initialize database and start worker pool on startup"""
    global worker_pool
    await init_db()
    worker_pool = WorkerPool()
    await worker_pool.start()
    print("✅ Database initialized and Worker Pool started")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop worker pool on shutdown"""
    if worker_pool:
        await worker_pool.stop()
    print("🛑 Worker Pool stopped")

@app.get("/")
async def root():
    return {
        "message": "Task Processing System API",
        "version": "1.0.0",
        "endpoints": {
            "submit_task": "POST /tasks",
            "get_task_status": "GET /tasks/{task_id}",
            "get_all_tasks": "GET /tasks",
            "get_task_result": "GET /tasks/{task_id}/result",
            "get_stats": "GET /stats",
            "get_detailed_stats": "GET /stats/detailed"
        }
    }

@app.post("/tasks", response_model=TaskResponse, status_code=201)
async def submit_task(
    task_data: TaskCreate,
    db: AsyncSession = Depends(get_db)
):
    """Submit a new task to the queue"""
    try:
        # Create new task
        new_task = Task(
            task_type=task_data.task_type,
            payload=json.dumps(task_data.payload),
            status=TaskStatus.PENDING
        )
        
        db.add(new_task)
        await db.commit()
        await db.refresh(new_task)
        
        # Notify worker pool about new task
        if worker_pool:
            await worker_pool.notify_new_task()
        
        return new_task
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")

@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task_status(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get status of a specific task"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task

@app.get("/tasks", response_model=List[TaskResponse])
async def get_all_tasks(
    status: TaskStatus = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get all tasks, optionally filtered by status"""
    query = select(Task)
    
    if status:
        query = query.where(Task.status == status)
    
    query = query.limit(limit).order_by(Task.created_at.desc())
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    return tasks

@app.get("/tasks/{task_id}/result")
async def get_task_result(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get the result of a completed task"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status == TaskStatus.PENDING or task.status == TaskStatus.PROCESSING:
        return {
            "status": task.status.value,
            "message": "Task is still processing"
        }
    
    if task.status == TaskStatus.FAILED:
        return {
            "status": task.status.value,
            "error": task.error_message,
            "retry_count": task.retry_count
        }
    
    return {
        "status": task.status.value,
        "result": json.loads(task.result) if task.result else None,
        "completed_at": task.completed_at
    }

@app.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get system statistics"""
    
    stats = {}
    
    for status in TaskStatus:
        result = await db.execute(
            select(Task).where(Task.status == status)
        )
        count = len(result.scalars().all())
        stats[status.value] = count
    
    return {
        "statistics": stats,
        "worker_pool_size": worker_pool.pool_size if worker_pool else 0,
        "active_workers": len(worker_pool.workers) if worker_pool else 0
    }

@app.get("/stats/detailed")
async def get_detailed_stats(db: AsyncSession = Depends(get_db)):
    """Get detailed system statistics with performance metrics"""
    
    stats = {}
    
    # Count by status
    for status in TaskStatus:
        result = await db.execute(
            select(func.count(Task.id)).where(Task.status == status)
        )
        count = result.scalar()
        stats[status.value] = count
    
    # Average processing time
    result = await db.execute(
        select(
            func.avg(
                func.extract('epoch', Task.completed_at - Task.created_at)
            )
        ).where(Task.status == TaskStatus.COMPLETED)
    )
    avg_time = result.scalar() or 0
    
    # Tasks per minute (last hour)
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    result = await db.execute(
        select(func.count(Task.id)).where(Task.created_at >= one_hour_ago)
    )
    tasks_last_hour = result.scalar()
    tasks_per_minute = tasks_last_hour / 60 if tasks_last_hour else 0
    
    # Success rate
    result_completed = await db.execute(
        select(func.count(Task.id)).where(Task.status == TaskStatus.COMPLETED)
    )
    completed = result_completed.scalar()
    
    result_failed = await db.execute(
        select(func.count(Task.id)).where(Task.status == TaskStatus.FAILED)
    )
    failed = result_failed.scalar()
    
    total_finished = completed + failed
    success_rate = (completed / total_finished * 100) if total_finished > 0 else 0
    
    return {
        "status_breakdown": stats,
        "performance": {
            "avg_processing_time_seconds": round(avg_time, 2),
            "tasks_per_minute": round(tasks_per_minute, 2),
            "tasks_last_hour": tasks_last_hour,
            "success_rate_percent": round(success_rate, 2)
        },
        "worker_pool": {
            "pool_size": worker_pool.pool_size if worker_pool else 0,
            "active_workers": len(worker_pool.workers) if worker_pool else 0
        }
    }

@app.delete("/tasks/{task_id}")
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a task (only if completed or failed)"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status in [TaskStatus.PENDING, TaskStatus.PROCESSING]:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete task that is pending or processing"
        )
    
    await db.delete(task)
    await db.commit()
    
    return {"message": f"Task {task_id} deleted successfully"}