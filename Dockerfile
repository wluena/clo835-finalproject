# Use a more efficient, lightweight Python base image 
FROM python:3.9-slim

# Set the working directory inside the container 
WORKDIR /app

# Install system dependencies (mysql-client is needed for DB interaction) 
RUN apt-get update && apt-get install -y \
    mariadb-client \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies 
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code 
COPY . .

# Create the static folder and set permissions so the app can save the S3 image locally 
RUN mkdir -p static && chmod 777 static

# Your Flask application MUST listen on port 81 
EXPOSE 81

# Set the command to run your app 
CMD [ "python", "app.py" ]