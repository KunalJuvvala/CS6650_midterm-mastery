"""
locustfile.py - Experiment 3: step load against the gateway to watch auto scaling.

Run from the midterm-mastery folder:
  locust -f scripts/locustfile.py --host http://<gateway address> --headless \
         --csv exp3-scaling/locust --html exp3-scaling/locust_report.html

The StepLoad shape sets the number of users by itself (about 12 minutes).
A 503 ("gateway is busy") is counted as a failure so it stands out in the charts.
"""
import os

from locust import HttpUser, LoadTestShape, between, task

FILE_NAME = os.getenv("FILE_NAME", "size-1k.txt")


class FileUser(HttpUser):
    wait_time = between(0.5, 1.5)

    @task
    def get_file(self):
        with self.client.get(f"/files?name={FILE_NAME}", name="GET /files",
                             catch_response=True, timeout=70) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 503:
                response.failure("503 gateway busy / backend rejected")
            elif response.status_code == 504:
                response.failure("504 backend did not respond")
            else:
                response.failure(f"status {response.status_code}")


class StepLoad(LoadTestShape):
    # (end time in seconds, number of users, users started per second)
    steps = [
        (180, 5, 1),
        (360, 15, 2),
        (540, 40, 5),
        (720, 5, 5),
    ]

    def tick(self):
        run_time = self.get_run_time()
        for end, users, spawn_rate in self.steps:
            if run_time < end:
                return users, spawn_rate
        return None
