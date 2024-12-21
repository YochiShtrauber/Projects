# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt into the container
COPY requirements.txt /app/requirements.txt

# Install the dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the content of the source code to the container
COPY . /app/

# Expose port 8000
EXPOSE 8000


# Command to run the FastAPI app with Dapr sidecar and uvicorn
#CMD ["uvicorn", "news_accessor:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
CMD ["python", "news.py"]