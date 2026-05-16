import streamlit as st
import cv2
import numpy as np
from PIL import Image
import pytesseract
import pandas as pd
from pdf2image import convert_from_bytes
import io

# Optional: Import PaddleOCR for advanced extraction
try:
    from paddleocr import PaddleOCR
    PADDLE_AVAILABLE = True
except ImportError:
    PADDLE_AVAILABLE = False

st.set_page_config(page_title="Image to Editable UI", layout="wide")

@st.cache_resource
def load_paddle_ocr():
    if PADDLE_AVAILABLE:
        # Initialize PaddleOCR (English language, download models automatically)
        return PaddleOCR(use_angle_cls=True, lang='en')
    return None

paddle_ocr = load_paddle_ocr()

def process_pdf(file_bytes):
    """Convert uploaded PDF bytes to a list of PIL Images."""
    images = convert_from_bytes(file_bytes)
    return images

def extract_text_tesseract(image):
    """Extract text and bounding boxes using Tesseract."""
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    results = []
    for i in range(len(data['text'])):
        if int(data['conf'][i]) > 40 and data['text'][i].strip() != "":
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            results.append({
                "Text": data['text'][i],
                "Confidence": data['conf'][i],
                "Box": [x, y, w, h]
            })
    return results

def extract_text_paddle(image_np):
    """Extract text using PaddleOCR for better formatting detection."""
    result = paddle_ocr.ocr(image_np, cls=True)
    results = []
    if result[0]:
        for line in result[0]:
            box = line[0]
            text = line[1][0]
            confidence = line[1][1]
            
            # Convert Paddle polygon box to x, y, w, h
            x_coords = [point[0] for point in box]
            y_coords = [point[1] for point in box]
            x, y = min(x_coords), min(y_coords)
            w, h = max(x_coords) - x, max(y_coords) - y
            
            results.append({
                "Text": text,
                "Confidence": float(confidence) * 100,
                "Box": [int(x), int(y), int(w), int(h)]
            })
    return results

def extract_shapes(image_np):
    """Use OpenCV to find non-text objects (geometric shapes, boundaries)."""
    gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    shapes = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 500: # Filter out tiny noise
            x, y, w, h = cv2.boundingRect(cnt)
            shapes.append([x, y, w, h])
    return shapes

# --- UI Layout ---
st.title("📄 Image & Diagram to Editable Output")
st.markdown("Upload scientific figures, scanned PDFs, or diagrams to extract editable text and object layers.")

# Sidebar Controls
st.sidebar.header("Extraction Settings")
ocr_engine = st.sidebar.radio("OCR Engine", ["PaddleOCR (Advanced)", "Tesseract (Standard)"] if PADDLE_AVAILABLE else ["Tesseract (Standard)"])
extract_geometric = st.sidebar.checkbox("Extract Geometric Shapes & Boxes", value=True)

# File Uploader
uploaded_files = st.file_uploader(
    "Drag and drop images or PDFs here", 
    type=['png', 'jpg', 'jpeg', 'pdf', 'tiff', 'svg'], 
    accept_multiple_files=True
)

if uploaded_files:
    for uploaded_file in uploaded_files:
        st.write("---")
        st.subheader(f"Processing: {uploaded_file.name}")
        
        # Load Image(s)
        images_to_process = []
        if uploaded_file.name.lower().endswith('.pdf'):
            pdf_images = process_pdf(uploaded_file.read())
            images_to_process.extend(pdf_images)
        else:
            image = Image.open(uploaded_file).convert('RGB')
            images_to_process.append(image)

        for i, img in enumerate(images_to_process):
            if len(images_to_process) > 1:
                st.markdown(f"**Page {i+1}**")
                
            img_np = np.array(img)
            
            # --- Processing Pipeline ---
            with st.spinner("Extracting objects and text..."):
                # 1. OCR Extraction
                if "Paddle" in ocr_engine:
                    text_data = extract_text_paddle(img_np)
                else:
                    text_data = extract_text_tesseract(img)
                
                # 2. Shape Extraction
                shape_data = extract_shapes(img_np) if extract_geometric else []

            # --- Visualization & Editing ---
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Original Preview (with detected layers)**")
                # Draw bounding boxes for visualization
                preview_img = img_np.copy()
                for item in text_data:
                    x, y, w, h = item["Box"]
                    cv2.rectangle(preview_img, (x, y), (x+w, y+h), (0, 255, 0), 2) # Green for text
                
                for shape in shape_data:
                    x, y, w, h = shape
                    cv2.rectangle(preview_img, (x, y), (x+w, y+h), (255, 0, 0), 2) # Blue for shapes
                    
                st.image(preview_img, channels="BGR", use_column_width=True)

            with col2:
                st.markdown("**Editable Extracted Data**")
                if text_data:
                    df = pd.DataFrame(text_data)
                    # Display as an editable dataframe
                    edited_df = st.data_editor(
                        df[["Text", "Confidence"]], 
                        num_rows="dynamic",
                        use_container_width=True,
                        key=f"editor_{uploaded_file.name}_{i}"
                    )
                    
                    st.download_button(
                        label="Download Edited Text as CSV",
                        data=edited_df.to_csv(index=False).encode('utf-8'),
                        file_name=f"{uploaded_file.name}_extracted.csv",
                        mime='text/csv'
                    )
                else:
                    st.info("No text detected.")
