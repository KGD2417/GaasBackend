#local_api
from fastapi import FastAPI
from worker import worker_status
from gpu import get_gpu_info
import threading
from worker import worker_loop

app = FastAPI(title="GAAS Worker")

@app.get("/status")
def status():
    return {
        "online": worker_status["online"],
        "current_job": worker_status["current_job"],
        "gpu": get_gpu_info()
    }

@app.post("/start")
def start_worker():
    if not worker_status["online"]:
        worker_status["online"] = True
        threading.Thread(target=worker_loop, daemon=True).start()
    return {"status": "started"}

@app.post("/stop")
def stop_worker():
    worker_status["online"] = False
    return {"status": "stopped"}

@app.get("/logs")
def logs():
    return {"logs": worker_status["logs"]}
