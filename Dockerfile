# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Install dependencies for ffmpeg and PortAudio
RUN apt-get update && \
    apt-get install -y \
    portaudio19-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*  # Clean up apt cache to reduce image size

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables for ffmpeg and ffprobe (optional, if required)
ENV PATH="/usr/local/bin:$PATH"

# Command to run the app
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
