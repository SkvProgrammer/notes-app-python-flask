# Use the official Python image as a base
FROM python:3.11-slim

# Set environment variables
# Prevents Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
# Ensures stdout and stderr are unbuffered
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY . /app/

# Expose the port Flask will run on
EXPOSE 5000

# Define the command to run the application
CMD ["python", "app.py"]
