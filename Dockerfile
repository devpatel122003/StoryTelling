# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Install PortAudio
RUN apt-get update && apt-get install -y portaudio19-dev

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install Python dependencies
RUN pip install -r requirements.txt

# Command to run the app
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
