import asyncio
import aiohttp
import time
from collections import defaultdict

async def test_reliability(num_tasks=500):
    """Test system reliability - should achieve 99%+ success rate"""
    
    print(f"\n{'='*60}")
    print(f"RELIABILITY TEST: Testing {num_tasks} tasks")
    print(f"{'='*60}\n")
    
    results = {
        "submitted": 0,
        "completed": 0,
        "failed": 0,
        "pending": 0,
        "processing": 0,
        "retrying": 0
    }
    
    task_ids = []
    
    async with aiohttp.ClientSession() as session:
        # Submit all tasks
        print("📤 Submitting tasks...")
        start_time = time.time()
        
        for i in range(num_tasks):
            payload = {
                "task_type": "data_processing",
                "payload": {"task_num": i}
            }
            
            try:
                async with session.post(
                    "http://localhost:8000/tasks",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 201:
                        result = await response.json()
                        task_ids.append(result["id"])
                        results["submitted"] += 1
            except Exception as e:
                print(f"❌ Failed to submit task {i}: {e}")
        
        submit_time = time.time() - start_time
        print(f"✅ Submitted {results['submitted']}/{num_tasks} tasks in {submit_time:.2f}s")
        
        # Wait for processing
        print("\n⏳ Waiting 60 seconds for tasks to process...")
        await asyncio.sleep(60)
        
        # Check status of all tasks
        print("\n🔍 Checking task status...")
        
        for task_id in task_ids:
            try:
                async with session.get(
                    f"http://localhost:8000/tasks/{task_id}",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        task = await response.json()
                        status = task["status"]
                        results[status] += 1
            except Exception as e:
                print(f"❌ Failed to check task {task_id}: {e}")
        
        # Calculate reliability
        total_checked = sum([
            results["completed"],
            results["failed"],
            results["pending"],
            results["processing"],
            results["retrying"]
        ])
        
        reliability = (results["completed"] / total_checked * 100) if total_checked > 0 else 0
        
        # Print results
        print(f"\n{'='*60}")
        print("📊 RELIABILITY TEST RESULTS")
        print(f"{'='*60}")
        print(f"Total Submitted:  {results['submitted']}")
        print(f"Completed:        {results['completed']} ({results['completed']/total_checked*100:.2f}%)")
        print(f"Failed:           {results['failed']} ({results['failed']/total_checked*100:.2f}%)")
        print(f"Still Processing: {results['processing']}")
        print(f"Pending:          {results['pending']}")
        print(f"Retrying:         {results['retrying']}")
        print(f"\n{'='*60}")
        print(f"🎯 RELIABILITY SCORE: {reliability:.2f}%")
        print(f"{'='*60}")
        
        if reliability >= 99.0:
            print("✅ TARGET ACHIEVED: 99%+ reliability!")
        else:
            print(f"⚠️  Below target. Need {99.0 - reliability:.2f}% improvement")
        
        return reliability

if __name__ == "__main__":
    asyncio.run(test_reliability(500))