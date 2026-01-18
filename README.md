# Concurrent Task Processing System

A high-performance task queue system built with Python, FastAPI, and PostgreSQL that handles 1000+ concurrent requests per minute with 99%+ reliability.

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 🚀 Features

- **High Performance**: Handles 1,299+ requests per minute
- **99%+ Reliability**: Achieved 100% success rate in testing
- **Scalable Architecture**: 50 concurrent workers using asyncio
- **Automatic Retry Logic**: 3 attempts with intelligent error handling
- **RESTful API**: 7 production-ready endpoints
- **Real-time Monitoring**: Detailed statistics and performance metrics
- **PostgreSQL Backend**: Persistent task storage with async operations

## 📊 Performance Metrics
```
✅ Throughput: 1,299 requests/minute
✅ Reliability: 100% (500/500 tasks completed)
✅ Average Response Time: 46ms
✅ Concurrent Workers: 50
✅ Retry Success Rate: 99%+
```

## 🏗️ Architecture
```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   FastAPI   │────▶│  Task Queue  │────▶│   Workers   │
│     API     │     │  (Database)  │     │   (Pool)    │
└─────────────┘     └──────────────┘     └─────────────┘
       │                    │                     │
       │                    │                     │
       ▼                    ▼                     ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  REST APIs  │     │  PostgreSQL  │     │   Asyncio   │
└─────────────┘     └──────────────┘     └─────────────┘
```

## 🛠️ Tech Stack

- **Backend**: Python 3.11+, FastAPI
- **Database**: PostgreSQL with asyncpg
- **ORM**: SQLAlchemy (async)
- **Concurrency**: asyncio
- **Testing**: pytest, Locust, aiohttp
- **Validation**: Pydantic

## 📦 Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- pip

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/task-processing-system.git
cd task-processing-system
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your PostgreSQL credentials
```

5. **Create database**
```sql
CREATE DATABASE task_queue_db;
```

6. **Run the application**
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## 📖 API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Main Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/tasks` | Submit a new task |
| GET | `/tasks/{task_id}` | Get task status |
| GET | `/tasks/{task_id}/result` | Get task result |
| GET | `/tasks` | List all tasks |
| GET | `/stats` | System statistics |
| GET | `/stats/detailed` | Detailed performance metrics |
| DELETE | `/tasks/{task_id}` | Delete a task |

### Example Usage

**Submit a task:**
```bash
curl -X POST "http://localhost:8000/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "data_processing",
    "payload": {"data": "example"}
  }'
```

**Check task status:**
```bash
curl "http://localhost:8000/tasks/1"
```

**Get task result:**
```bash
curl "http://localhost:8000/tasks/1/result"
```

## 🧪 Testing

### Run Performance Tests
```bash
python tests/performance_test.py
```

### Run Reliability Tests
```bash
python tests/reliability_test.py
```

### Run Load Tests (Locust)
```bash
locust -f tests/load_test.py --host=http://localhost:8000
# Open http://localhost:8089
```

## ⚙️ Configuration

Edit `.env` file:
```env
DATABASE_URL=postgresql://postgres:password@localhost/task_queue_db
WORKER_POOL_SIZE=50
MAX_RETRIES=3
```

### Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | - |
| `WORKER_POOL_SIZE` | Number of concurrent workers | 50 |
| `MAX_RETRIES` | Maximum retry attempts | 3 |
| `RETRY_DELAY` | Delay between retries (seconds) | 5 |

## 📁 Project Structure
```
task-processing-system/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application
│   ├── worker.py         # Worker pool implementation
│   ├── models.py         # Database models
│   ├── database.py       # Database connection
│   ├── schemas.py        # Pydantic schemas
│   └── config.py         # Configuration
├── tests/
│   ├── __init__.py
│   ├── performance_test.py
│   ├── reliability_test.py
│   └── load_test.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## 🔧 Customizing Task Types

Add custom task types in `app/worker.py`:
```python
async def execute_task(self, task: Task):
    payload = json.loads(task.payload)
    
    if task.task_type == "your_custom_task":
        # Your custom logic here
        result = await your_custom_function(payload)
        return {"status": "completed", "result": result}
```

## 🚀 Deployment

### Docker (Coming Soon)
```bash
docker-compose up -d
```

### Production Considerations

- Use a production WSGI server (e.g., Gunicorn with Uvicorn workers)
- Set up database connection pooling
- Configure logging and monitoring
- Enable HTTPS
- Set up rate limiting
- Add authentication/authorization

## 📈 Performance Optimization Tips

1. **Increase worker pool size** for higher throughput
2. **Adjust task processing times** based on your use case
3. **Use connection pooling** for database operations
4. **Enable caching** for frequently accessed data
5. **Monitor and tune PostgreSQL** settings

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👤 Author
Auromira J

- GitHub: [@Auromirajayakumar](https://github.com/auromirajayakumar)
- LinkedIn: [Auromirajayakumar](https://linkedin.com/in/auromira-jayakumar-1805aa2a9)

## 🙏 Acknowledgments

- FastAPI for the amazing framework
- PostgreSQL for reliable data persistence
- The Python async community

---

**⭐ If you found this project helpful, please give it a star!**