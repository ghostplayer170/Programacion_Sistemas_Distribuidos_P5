# Use image of Python 3.9 slim version as base image
FROM python:3.9-slim

# Establish the working directory
WORKDIR /app

# Copy the requirements file to the working directory and install the dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code to the working directory
COPY . .

# Expose the port 80
EXPOSE 80

# Run the application
CMD ["python", "node.py"]
