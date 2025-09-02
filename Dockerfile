# Use the official Python image as the base
FROM python:3.10-slim

# Install dependencies for OrpheusDL
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ffmpeg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install OrpheusDL and the Tidal module
RUN pip install OrpheusDL

# Install Rclone
RUN curl https://rclone.org/install.sh | bash

# Copy required files into the container
WORKDIR /app
COPY requirements.txt .
COPY bot.py .
COPY rclone.conf /root/.config/rclone/rclone.conf

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create a dedicated directory for downloads
RUN mkdir -p /app/downloads

# Set the entrypoint to run the bot script
CMD ["python", "bot.py"]
