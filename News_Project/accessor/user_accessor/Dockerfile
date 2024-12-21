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

# Expose ports for FastAPI (5001)
EXPOSE 5001

# Start both FastAPI app and the gRPC server in the same container
CMD ["sh", "-c", "python -m service_grpc_server & uvicorn App:app --host 0.0.0.0 --port 5001 --reload"]
