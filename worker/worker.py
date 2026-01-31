# worker.py

import requests
import time
import uuid
import os
from executor import execute_job

BACKEND = "http://localhost:8000"
WORKER_ID_FILE = "worker_id.txt"

# ----------------------------
# Persistent Worker ID
# ----------------------------
if os.path.exists(WORKER_ID_FILE):
    with open(WORKER_ID_FILE, "r") as f:
        WORKER_ID = f.read().strip()
else:
    WORKER_ID = str(uuid.uuid4())
    with open(WORKER_ID_FILE, "w") as f:
        f.write(WORKER_ID)

# ----------------------------
# Worker Status
# ----------------------------
worker_status = {
    "online": False,
    "current_job": None,
    "logs": ""
}

# ----------------------------
# Worker Loop
# ----------------------------
def worker_loop():
    global worker_status

    while worker_status["online"]:

        try:
            # Ask backend for job
            response = requests.post(
                f"{BACKEND}/job/assign",
                params={"worker_id": WORKER_ID},
                timeout=5
            )

            if response.status_code != 200:
                worker_status["logs"] = "\nFailed to contact backend."
                time.sleep(5)
                continue

            data = response.json()
            job = data.get("job")

            if job is None:
                time.sleep(5)
                continue

            job_id = job["job_id"]
            worker_status["current_job"] = job_id
            worker_status["logs"] = f"\nStarting job {job_id}...\n"

            # Execute job
            result = execute_job(job)

            stdout = result.get("stdout", "")
            stderr = result.get("stderr", "")
            model_file = result.get("model_file")

            worker_status["logs"] += stdout + stderr

            # Limit log size
            if len(worker_status["logs"]) > 50000:
                worker_status["logs"] = worker_status["logs"][-50000:]

            # Send result to backend
            complete_response = requests.post(
                f"{BACKEND}/job/complete",
                json={
                    "job_id": job_id,
                    "output": worker_status["logs"],
                    "worker_id": WORKER_ID,
                    "success": stderr == "",
                    "model_file": model_file
                },
                timeout=10
            )

            if complete_response.status_code != 200:
                worker_status["logs"] += "\nFailed to submit job result."

            worker_status["current_job"] = None

        except requests.exceptions.Timeout:
            worker_status["logs"] = "\nBackend timeout."
        except Exception as e:
            worker_status["logs"] = f"\nERROR: {str(e)}"

        time.sleep(3)
