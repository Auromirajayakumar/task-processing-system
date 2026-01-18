from locust import HttpUser, task, between
import random
import json

class TaskProcessingUser(HttpUser):
    wait_time = between(0.1, 0.5)  # Simulate realistic user behavior
    
    def on_start(self):
        """Called when a user starts"""
        self.task_ids = []
    
    @task(10)  # Weight: 10 (most common operation)
    def submit_task(self):
        """Submit a new task"""
        task_types = ["email", "data_processing", "report_generation"]
        
        payload = {
            "task_type": random.choice(task_types),
            "payload": {
                "id": random.randint(1000, 9999),
                "data": f"test_data_{random.randint(1, 1000)}"
            }
        }
        
        with self.client.post(
            "/tasks",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 201:
                task_id = response.json().get("id")
                self.task_ids.append(task_id)
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(5)  # Weight: 5
    def check_task_status(self):
        """Check status of a random task"""
        if self.task_ids:
            task_id = random.choice(self.task_ids)
            with self.client.get(
                f"/tasks/{task_id}",
                catch_response=True
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Failed with status {response.status_code}")
    
    @task(3)  # Weight: 3
    def get_task_result(self):
        """Get result of a random task"""
        if self.task_ids:
            task_id = random.choice(self.task_ids)
            with self.client.get(
                f"/tasks/{task_id}/result",
                catch_response=True
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Failed with status {response.status_code}")
    
    @task(2)  # Weight: 2
    def get_all_tasks(self):
        """Get all tasks"""
        with self.client.get(
            "/tasks?limit=50",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(1)  # Weight: 1
    def get_stats(self):
        """Get system statistics"""
        with self.client.get(
            "/stats",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")