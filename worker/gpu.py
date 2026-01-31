# gpu.py
import subprocess
import json

def get_gpu_info():
    try:
        # Query GPU info using nvidia-smi
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,memory.used,utilization.gpu",
                "--format=csv,noheader,nounits"
            ],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return {
                "gpu_name": None,
                "vram_total_mb": 0,
                "vram_used_mb": 0,
                "utilization_percent": 0,
                "cuda": False
            }

        lines = result.stdout.strip().split("\n")

        gpus = []
        for line in lines:
            name, total_mem, used_mem, utilization = [x.strip() for x in line.split(",")]

            gpus.append({
                "gpu_name": name,
                "vram_total_mb": int(total_mem),
                "vram_used_mb": int(used_mem),
                "utilization_percent": int(utilization),
                "cuda": True
            })

        return {
            "available": True,
            "gpu_count": len(gpus),
            "gpus": gpus
        }

    except FileNotFoundError:
        return {
            "available": False,
            "error": "nvidia-smi not found (No NVIDIA GPU or drivers not installed)"
        }

    except Exception as e:
        return {
            "available": False,
            "error": str(e)
        }
