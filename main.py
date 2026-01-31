#main.py
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import base64
import uuid
from typing import Dict, Optional
from datetime import datetime

app = FastAPI(title="GAAS Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------
# In-memory job store (DB later)
# ---------------------------------
jobs: Dict[str, dict] = {}

# ---------------------------------
# Models
# ---------------------------------

class JobAssignResponse(BaseModel):
    job: Optional[dict]

class JobResult(BaseModel):
    job_id: str
    output: str
    worker_id: str
    success: bool = True
    model_file: Optional[str] = None   # 🔥 ADD THIS



# =================================
# 🔥 SUBMIT JOB FROM FLUTTER
# =================================
@app.post("/job/submit")
async def submit_job(
    gpu_size: str = Form(...),
    requirements: str = Form(""),
    dataset: UploadFile = File(None),
    model_file: UploadFile = File(None),
    python_code: str = Form(None),
    
):
    job_id = str(uuid.uuid4())
    files_dict = {}

    # Dataset
    if dataset:
        dataset_bytes = await dataset.read()
        files_dict["dataset.csv"] = base64.b64encode(dataset_bytes).decode()

    # Model file upload
    if model_file:
        model_bytes = await model_file.read()
        files_dict["model.py"] = base64.b64encode(model_bytes).decode()

    # Inline Python code (overrides file)
    if python_code:
        files_dict["model.py"] = base64.b64encode(
            python_code.encode()
        ).decode()

    if "model.py" not in files_dict:
        raise HTTPException(status_code=400, detail="Model code is required")

    jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "assigned_worker": None,
        "gpu_size": gpu_size,
        "requirements": requirements.split(),
        "files": files_dict,
        "result": None,
        "error": None,
        "created_at": datetime.utcnow(),
        "started_at": None,
        "completed_at": None,
        "model_file": None

    }

    return {"job_id": job_id, "status": "queued"}


# =================================
# WORKER ASSIGN
# =================================
@app.post("/job/assign", response_model=JobAssignResponse)
def assign_job(worker_id: str):
    for job in jobs.values():
        if job["status"] == "queued":
            job["status"] = "running"
            job["assigned_worker"] = worker_id
            job["started_at"] = datetime.utcnow()
            return {"job": job}

    return {"job": None}


# =================================
# WORKER COMPLETE
# =================================
@app.post("/job/complete")
def complete_job(result: JobResult):
    job = jobs.get(result.job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["assigned_worker"] != result.worker_id:
        raise HTTPException(status_code=403, detail="Not your job")

    if job["status"] != "running":
        raise HTTPException(status_code=400, detail="Job not running")

    job["completed_at"] = datetime.utcnow()

    if result.success:
        job["status"] = "completed"
        job["result"] = result.output
        job["model_file"] = result.model_file   # 🔥 SAVE MODEL
    else:
        job["status"] = "failed"
        job["error"] = result.output


    return {"status": job["status"], "job_id": result.job_id}


# =================================
# GET JOB STATUS (Flutter Polling)
# =================================
@app.get("/job/{job_id}")
def get_job(job_id: str):
    job = jobs.get(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


# =================================
# DEBUG ENDPOINT
# =================================
@app.get("/jobs")
def list_jobs():
    return {"jobs": list(jobs.values())}
