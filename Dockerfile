# Use the official Python image as the base
FROM python:3.10-slim

# Install system dependencies for Pyrogram and FFmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ffmpeg \
    ca-certificates \
    libsecret-1-0 \
    && rm -rf /var/lib/apt/lists/*

# Install OrpheusDL and Pyrogram
RUN pip install OrpheusDL Pyrogram tgcrypto

# Install Rclone
RUN curl https://rclone.org/install.sh | bash

# Create directories and set the working directory
WORKDIR /app
COPY requirements.txt .
COPY bot.py .
COPY rclone.conf /root/.config/rclone/rclone.conf
RUN mkdir -p /app/downloads

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set the entrypoint to run the bot script
CMD ["python", "bot.py"]
