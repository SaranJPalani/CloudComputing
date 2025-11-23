FROM python:3.11-slim

# Install FFmpeg and OpenCV dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg libgl1 libglib2.0-0 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy backend requirements
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy all project files
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Copy ML models (place these files in project root before building)
# If missing, app will automatically use rule-based fallback
COPY crf_model.pkl preset_model.pkl ./ 

# Create upload/output directories
RUN mkdir -p uploads outputs

# Expose port for Flask
EXPOSE 5000

# Run the Flask app
CMD ["python", "backend/app.py"]
