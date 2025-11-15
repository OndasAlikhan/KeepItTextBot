# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies including ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the Hugging Face model during build
RUN python -c "from transformers import AutoModel, AutoTokenizer; \
    model_name='openai/whisper-small'; \
    AutoModel.from_pretrained(model_name); \
    AutoTokenizer.from_pretrained(model_name)"

# Copy project files
COPY . .

# Create a non-root user and switch to it
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port (adjust as needed)
EXPOSE 8080

# Run the application
CMD ["python", "main.py"]