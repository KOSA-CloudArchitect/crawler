# Dockerfile (Final Version for ARM64 with Chrome compatibility)

# 1. Base Image: Use Python 3.11-slim
FROM python:3.11-slim

# 2. Set Working Directory
WORKDIR /app

# 3. Install Chromium for ARM64 compatibility
#    (undetected-chromedriver will use this as a base)
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    xvfb \
    unzip \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 4. Copy and install Python libraries
#    (Ensure undetected-chromedriver is in your requirements.txt)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy Source Code
COPY src/ ./src/

# 6. Set Ports and Environment Variables
EXPOSE 8000
ENV PYTHONPATH=/app/src
ENV DISPLAY=:99

# 7. Healthcheck and Application Command
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/proxy/status || exit 1

WORKDIR /app/src
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
