import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:Auromira123@localhost/task_queue_db")
    WORKER_POOL_SIZE: int = int(os.getenv("WORKER_POOL_SIZE", "10"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY: int = 5  # seconds
    
settings = Settings()