FROM python:3.10-slim

        # Install system dependencies required for dlib
        RUN apt-get update && apt-get install -y \
            build-essential \
            cmake \
            libopenblas-dev \
            liblapack-dev \
            libx11-dev \
            && rm -rf /var/lib/apt/lists/*

        WORKDIR /app
        COPY . /app
        RUN pip install --no-cache-dir -r requirements.txt
        CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]
        ```

3.  **Change Service Type on Render**:
    *   In your Render settings for this web service, look for **Environment** or **Language**.
    *   Change it from **Python** to **Docker**.

### If it still crashes:
The harsh truth of cloud computing is that `dlib` simply requires significant RAM to run. If Render's Free Tier (which usually offers 512MB to 1GB) cannot handle even the *running* of the face recognition models, you may need to:
*   **Upgrade your Render instance** to a paid "Starter" plan ($7/mo) which offers more RAM.
*   **Switch to PythonAnywhere**, which has these libraries pre-installed in their OS image, so you never have to "build" them.

Try the `requirements.txt` change first—it's the most likely way to sneak past the 8GB wall! Let me know which step you're on.
