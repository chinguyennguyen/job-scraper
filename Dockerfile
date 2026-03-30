# Start from an official Python image (slim = smaller download, no extras we don't need)
FROM python:3.11-slim

# Set the working directory inside the container
# All commands below run from here; your files will live here
WORKDIR /app

# Copy requirements.txt first — before the rest of your code
# This lets Docker cache the library install step separately
COPY requirements.txt .

# Install your Python libraries
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your project files into the container
COPY . .

# Document that the app listens on port 5000
EXPOSE 5000

# The command that runs when the container starts
CMD ["python", "app.py"]
