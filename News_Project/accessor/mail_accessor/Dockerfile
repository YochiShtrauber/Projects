# Use Python 3.11-slim as base image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the requirements.txt into the container
COPY requirements.txt /app/requirements.txt

# Install the dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt



# Copy the current directory content into the container
COPY . /app/

# Expose ports for FastAPI (8001)
EXPOSE 8003

# Command to run the FastAPI app with uvicorn
CMD ["uvicorn", "mail:app", "--host", "0.0.0.0", "--port", "8003", "--reload"]