# Stage 1: Build stage to compile heavy libraries
FROM python:3.10-slim AS builder

# Install system dependencies needed to compile dlib
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install requirements to the build stage
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Final lean runtime stage
FROM python:3.10-slim

# Install only the runtime libraries needed for dlib/Face ID to function
RUN apt-get update && apt-get install -y \
    libopenblas0 \
    liblapack3 \
    libx11-6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the installed python packages from the builder stage
COPY --from=builder /root/.local /root/.local
COPY . .

# Ensure scripts in .local/bin are usable
ENV PATH=/root/.local/bin:$PATH

# Run with a single worker and thread to stay under 512MB RAM
CMD ["gunicorn", "--workers", "1", "--threads", "1", "--bind", "0.0.0.0:10000", "app:app"]
