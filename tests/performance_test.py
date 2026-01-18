import asyncio
import aiohttp
import time
from datetime import datetime
import statistics

async def submit_task(session, task_num):
    """Submit a single task and measure response time"""
    start_time = time.time()
    
    payload = {
        "task_type": "data_processing",
        "payload": {
            "task_number": task_num,
            "data": f"test_data_{task_num}"
        }
    }
    
    try:
        async with session.post(
            "http://localhost:8000/tasks",
            json=payload
        ) as response:
            if response.status == 201:
                result = await response.json()
                elapsed = time.time() - start_time
                return {
                    "success": True,
                    "task_id": result["id"],
                    "response_time": elapsed
                }
            else:
                return {
                    "success": False,
                    "status": response.status,
                    "response_time": time.time() - start_time
                }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "response_time": time.time() - start_time
        }

async def run_concurrent_test(num_tasks, concurrency):
    """Run concurrent task submission test"""
    print(f"\n{'='*60}")
    print(f"Running test: {num_tasks} tasks with {concurrency} concurrent requests")
    print(f"{'='*60}\n")
    
    async with aiohttp.ClientSession() as session:
        start_time = time.time()
        
        # Create batches of concurrent requests
        tasks = []
        for i in range(num_tasks):
            tasks.append(submit_task(session, i))
            
            # Execute in batches to control concurrency
            if len(tasks) >= concurrency:
                results = await asyncio.gather(*tasks)
                tasks = []
        
        # Execute remaining tasks
        if tasks:
            results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        return total_time

async def main():
    """Main performance testing function"""
    
    # Test 1: 100 requests with 10 concurrent
    print("\n🚀 TEST 1: Warmup Test")
    await run_concurrent_test(100, 10)
    
    # Test 2: 1000 requests with 50 concurrent
    print("\n🚀 TEST 2: 1000 Concurrent Requests")
    time_1000 = await run_concurrent_test(1000, 50)
    
    requests_per_minute = (1000 / time_1000) * 60
    print(f"\n✅ Results:")
    print(f"   - Total time: {time_1000:.2f} seconds")
    print(f"   - Requests per minute: {requests_per_minute:.2f}")
    print(f"   - Average response time: {(time_1000/1000)*1000:.2f}ms")
    
    # Test 3: 5000 requests with 100 concurrent
    print("\n🚀 TEST 3: 5000 Concurrent Requests (Stress Test)")
    time_5000 = await run_concurrent_test(5000, 100)
    
    requests_per_minute_5000 = (5000 / time_5000) * 60
    print(f"\n✅ Results:")
    print(f"   - Total time: {time_5000:.2f} seconds")
    print(f"   - Requests per minute: {requests_per_minute_5000:.2f}")
    print(f"   - Average response time: {(time_5000/5000)*1000:.2f}ms")
    
    print(f"\n{'='*60}")
    print("✅ PERFORMANCE TEST COMPLETED")
    print(f"{'='*60}")

if __name__ == "__main__":
    asyncio.run(main())