FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system build dependencies for native C/C++ packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from either backend/requirements.txt (root context) or requirements.txt (backend context)
COPY backend/requirements.txt* requirements.txt* ./

RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Ensure main.py and core/ are at /app root regardless of build context
RUN if [ -d "backend" ]; then cp -r backend/* . && rm -rf backend; fi

EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
