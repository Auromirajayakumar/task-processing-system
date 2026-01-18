import asyncio
import json
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.models import Task, TaskStatus
from app.config import settings

class WorkerPool:
    def __init__(self):
        self.pool_size = settings.WORKER_POOL_SIZE
        self.workers = []
        self.running = False
        self.task_queue = asyncio.Queue()
        
    async def start(self):
        """Start all workers in the pool"""
        self.running = True
        for i in range(self.pool_size):
            worker = asyncio.create_task(self.worker(i))
            self.workers.append(worker)
        
        # Start task fetcher
        self.task_fetcher = asyncio.create_task(self.fetch_pending_tasks())
        
    async def stop(self):
        """Stop all workers gracefully"""
        self.running = False
        
        # Cancel task fetcher
        if hasattr(self, 'task_fetcher'):
            self.task_fetcher.cancel()
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for cancellation
        await asyncio.gather(*self.workers, return_exceptions=True)
        
    async def fetch_pending_tasks(self):
        """Continuously fetch pending tasks from database"""
        while self.running:
            try:
                async with async_session_maker() as session:
                    result = await session.execute(
                        select(Task)
                        .where(Task.status == TaskStatus.PENDING)
                        .limit(self.pool_size * 2)
                    )
                    tasks = result.scalars().all()
                    
                    for task in tasks:
                        await self.task_queue.put(task.id)
                
                await asyncio.sleep(1)  # Check every second
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error fetching tasks: {e}")
                await asyncio.sleep(5)
    
    async def notify_new_task(self):
        """Called when a new task is submitted"""
        # Trigger immediate check for new tasks
        pass
    
    async def worker(self, worker_id: int):
        """Individual worker that processes tasks"""
        print(f"Worker {worker_id} started")
        
        while self.running:
            try:
                # Get task from queue with timeout
                task_id = await asyncio.wait_for(
                    self.task_queue.get(), 
                    timeout=5.0
                )
                
                await self.process_task(task_id, worker_id)
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Worker {worker_id} error: {e}")
    
    async def process_task(self, task_id: int, worker_id: int):
        """Process a single task with retry logic"""
        async with async_session_maker() as session:
            try:
                # Get task
                result = await session.execute(
                    select(Task).where(Task.id == task_id)
                )
                task = result.scalar_one_or_none()
                
                if not task or task.status != TaskStatus.PENDING:
                    return
                
                # Mark as processing
                task.status = TaskStatus.PROCESSING
                task.updated_at = datetime.utcnow()
                await session.commit()
                
                print(f"Worker {worker_id} processing task {task_id}")
                
                # Execute the actual task
                result = await self.execute_task(task)
                
                # Mark as completed
                task.status = TaskStatus.COMPLETED
                task.result = json.dumps(result)
                task.completed_at = datetime.utcnow()
                task.updated_at = datetime.utcnow()
                await session.commit()
                
                print(f"Worker {worker_id} completed task {task_id}")
                
            except Exception as e:
                # Handle failure with retry logic
                await self.handle_task_failure(session, task, str(e))
    
    async def execute_task(self, task: Task):
        """Execute the actual task logic - customize this based on task_type"""
        payload = json.loads(task.payload)
        
        # Simulate different task types with FASTER processing
        if task.task_type == "email":
            await asyncio.sleep(0.1)  # Changed from 2 to 0.1
            return {"status": "email_sent", "to": payload.get("email")}
        
        elif task.task_type == "data_processing":
            await asyncio.sleep(0.1)  # Changed from 3 to 0.1
            return {"status": "processed", "records": payload.get("count", 100)}
        
        elif task.task_type == "report_generation":
            await asyncio.sleep(0.5)  # Changed from 5 to 0.5
            return {"status": "generated", "report_id": f"RPT-{task.id}"}
        
        else:
            # Default task processing
            await asyncio.sleep(0.1)  # Changed from 1 to 0.1
            return {"status": "completed", "data": payload}
    
    async def handle_task_failure(self, session: AsyncSession, task: Task, error: str):
        """Handle task failure with retry logic"""
        task.retry_count += 1
        task.error_message = error
        task.updated_at = datetime.utcnow()
        
        if task.retry_count < settings.MAX_RETRIES:
            # Retry the task
            task.status = TaskStatus.RETRYING
            print(f"Task {task.id} failed, retrying ({task.retry_count}/{settings.MAX_RETRIES})")
            
            await session.commit()
            
            # Add back to queue after delay
            await asyncio.sleep(settings.RETRY_DELAY)
            await self.task_queue.put(task.id)
            
            # Reset to pending for retry
            task.status = TaskStatus.PENDING
            await session.commit()
        else:
            # Max retries reached
            task.status = TaskStatus.FAILED
            print(f"Task {task.id} failed permanently after {task.retry_count} retries")
            await session.commit()