# Use Python 3.11-slim as base image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy the requirements.txt into the container
COPY requirements.txt /app/requirements.txt

# Install the dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the current directory content into the container
COPY . /app/

# Expose ports for FastAPI
EXPOSE 5000

# Default command (can be overridden by docker-compose command)
CMD ["uvicorn", "manager:app", "--host", "0.0.0.0", "--port", "5000", "--reload"]
