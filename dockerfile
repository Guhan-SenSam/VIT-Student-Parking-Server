# Use the official Python image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code and .env file
COPY . .

# Expose the port FastAPI will run on
EXPOSE 5000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
