
        FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

        WORKDIR /app

        RUN apt-get update && apt-get install -y python3 python3-pip && \
            ln -s /usr/bin/python3 /usr/bin/python && \
            pip install --upgrade pip

        COPY requirements.txt /tmp/requirements.txt

        RUN if [ -f /tmp/requirements.txt ]; then pip install -r /tmp/requirements.txt; fi

        CMD ["python", "model.py"]
        