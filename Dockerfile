# Use the official Microsoft Playwright image with Python
FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (and system dependencies)
# We only need chromium for this project
RUN playwright install chromium --with-deps

# Copy project files
COPY . .

# Ensure logs appear in real-time
ENV PYTHONUNBUFFERED=1

# Ensure data directory exists
RUN mkdir -p data

# Environment variables will be handled by Koyeb UI
# Command to run the bot
CMD ["python", "auto_engine.py"]
