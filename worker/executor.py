import os
import base64
import subprocess
import uuid
import shutil
import shutil as sh
import platform

DOCKER_GPU_IMAGE = "nvidia/cuda:12.2.0-runtime-ubuntu22.04"
DOCKER_CPU_IMAGE = "python:3.10-slim"

def execute_job(job):
    job_id = job["job_id"]
    unique_id = uuid.uuid4().hex[:6]
    job_dir = os.path.abspath(os.path.join("jobs", f"{job_id}-{unique_id}"))

    print("\n==============================")
    print("🚀 STARTING EXECUTION")
    print("Job ID:", job_id)
    print("Job Dir:", job_dir)
    print("Docker Path:", sh.which("docker"))
    print("==============================\n")

    if not sh.which("docker"):
        return {"stdout": "", "stderr": "Docker not installed or not in PATH"}

    os.makedirs(job_dir, exist_ok=True)

    try:
        # -------------------------
        # Write Files
        # -------------------------
        print("📁 Writing files...")
        for name, content in job["files"].items():
            file_path = os.path.join(job_dir, name)
            with open(file_path, "wb") as f:
                f.write(base64.b64decode(content))

        # -------------------------
        # Write requirements.txt
        # -------------------------
        requirements = job.get("requirements", [])
        if requirements:
            with open(os.path.join(job_dir, "requirements.txt"), "w") as f:
                f.write("\n".join(requirements))

        # -------------------------
        # Detect GPU availability
        # -------------------------
        print("🔍 Checking GPU support...")
        gpu_test = subprocess.run(
            ["docker", "run", "--rm", "--gpus", "all", DOCKER_GPU_IMAGE, "nvidia-smi"],
            capture_output=True,
            text=True
        )

        use_gpu = gpu_test.returncode == 0
        base_image = DOCKER_GPU_IMAGE if use_gpu else DOCKER_CPU_IMAGE

        print("GPU Available:", use_gpu)
        print("Using Image:", base_image)

        # -------------------------
        # Create Dockerfile
        # IMPORTANT: NO COPY if mounting volume
        # -------------------------
        dockerfile_content = f"""
        FROM {base_image}

        WORKDIR /app

        RUN apt-get update && apt-get install -y python3 python3-pip && \\
            ln -s /usr/bin/python3 /usr/bin/python && \\
            pip install --upgrade pip

        COPY requirements.txt /tmp/requirements.txt

        RUN if [ -f /tmp/requirements.txt ]; then pip install -r /tmp/requirements.txt; fi

        CMD ["python", "model.py"]
        """

        dockerfile_path = os.path.join(job_dir, "Dockerfile")
        with open(dockerfile_path, "w") as f:
            f.write(dockerfile_content)

        print("📝 Dockerfile created")

        image_name = f"gaas-job-{job_id[:8]}-{unique_id}"
        container_name = f"gaas-container-{unique_id}"

        # -------------------------
        # Build Image
        # -------------------------
        print("🔨 Building image...")
        build = subprocess.run(
            ["docker", "build", "-t", image_name, "."],
            cwd=job_dir,
            capture_output=True,
            text=True
        )

        if build.returncode != 0:
            print("❌ Build Failed")
            print(build.stderr)
            return {"stdout": "", "stderr": build.stderr}

        print("✅ Image Built")

        # -------------------------
        # Format volume path (Windows fix)
        # -------------------------
        mount_path = job_dir
        if platform.system() == "Windows":
            mount_path = mount_path.replace("\\", "/")

        # -------------------------
        # Run Container
        # -------------------------
        print("▶ Running container...")

        run_cmd = [
            "docker", "run",
            "--rm",
            "--name", container_name,
            "--memory", "4g",
            "--cpus", "4",
            "--network", "none",
            "-v", f"{mount_path}:/app",
        ]

        if use_gpu:
            run_cmd.extend(["--gpus", "all"])

        run_cmd.append(image_name)

        print("Run Command:", " ".join(run_cmd))

        run = subprocess.run(
            run_cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=300
        )

        print("------ STDOUT ------")
        print(run.stdout)
        print("------ STDERR ------")
        print(run.stderr)

        # -------------------------
        # Detect model artifact
        # -------------------------
        print("🔍 Checking for trained model...")
        model_file_base64 = None

        for file_name in ["trained_model.pkl", "model.pkl", "model.pt", "model.h5"]:
            model_path = os.path.join(job_dir, file_name)
            if os.path.exists(model_path):
                print("✅ Found model:", model_path)
                with open(model_path, "rb") as f:
                    model_file_base64 = base64.b64encode(f.read()).decode()
                break

        # -------------------------
        # Cleanup image
        # -------------------------
        print("🧹 Removing image...")
        subprocess.run(["docker", "rmi", "-f", image_name], capture_output=True)

        print("✅ DONE\n")

        return {
            "stdout": run.stdout,
            "stderr": run.stderr,
            "model_file": model_file_base64
        }

    except subprocess.TimeoutExpired:
        print("⏰ Timeout")
        subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)
        return {"stdout": "", "stderr": "Execution timed out"}

    except Exception as e:
        print("🔥 ERROR:", str(e))
        return {"stdout": "", "stderr": str(e)}
