FROM python:3.10-slim AS builder

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install requirements + the missing models directly from source
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt
RUN pip install --user git+https://github.com/ageitgey/face_recognition_models

FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    libopenblas0 \
    liblapack3 \
    libx11-6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH

# Adding a timeout to give the heavy models time to load in memory
CMD ["gunicorn", "--workers", "1", "--threads", "1", "--timeout", "120", "--bind", "0.0.0.0:10000", "app:app"]
