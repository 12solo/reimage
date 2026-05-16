# Use official NVIDIA CUDA base image with Ubuntu 22.04 and CUDNN 8
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies
# 1. python3 & pip for our runtime environment
# 2. tesseract-ocr & poppler-utils for document parsing/OCR
# 3. libgl1-mesa-glx & libglib2.0-0 for OpenCV image processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3-pip \
    python3-dev \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    libgl1-mesa-glx \
    libglib2.0-0 \
    git \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set up the working directory inside the container
WORKDIR /app

# Upgrade pip and install wheel setup tools
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements first to leverage Docker's layer caching mechanism
COPY requirements.txt .

# Install heavy machine learning and frontend dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of the application files (app.py and src/ directory)
COPY . .

# Expose the default Streamlit network port
EXPOSE 8501

# Run the Streamlit application bound to all local network interfaces
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
