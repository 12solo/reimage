# 🧬 SciReImage Pro

An AI-powered, Adobe-like scientific image editor. Convert static journal figures, flowcharts, and presentation slides into fully editable layers using Segment Anything (SAM), Stable Diffusion, and Advanced OCR.

## Features
* 🪄 **Auto-Segmentation:** Breaks flat images into editable vector layers using Meta's SAM.
* 📝 **Scientific OCR:** Extracts formulas, subscripts, and text via PaddleOCR.
* 🎨 **NLP Editing:** Type "Make arrows blue" or "Replace icon with microscope" and the AI executes.
* 💾 **Workflow Export:** Export reconstructed images to `.pptx`, `.svg`, and Draw.io formats.

## System Requirements
* NVIDIA GPU (8GB+ VRAM recommended for Local execution)
* Docker & Docker Compose
* Minimum 16GB System RAM

## Installation (Docker)
The easiest way to run this application with all system dependencies (CUDA, Tesseract, Poppler) is via Docker.

1. Clone the repository:
   ```bash
   git clone [https://github.com/yourusername/scireimage-pro.git](https://github.com/yourusername/scireimage-pro.git)
   cd scireimage-pro
