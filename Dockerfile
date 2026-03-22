FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies if any of your python libs need to compile code
# RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Use a cache mount to speed up subsequent builds
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 8000

# Using --proxy-headers is important for your Nginx OAuth 'mismatching_state' issue!
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips='*'"]