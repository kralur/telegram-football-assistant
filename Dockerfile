FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Prevent python from buffering stdout
ENV PYTHONUNBUFFERED=1

# Install system dependencies (optional but good practice)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for Docker layer caching)
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Run bot
CMD ["python", "-m", "src.app"]