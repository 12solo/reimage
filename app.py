import streamlit as st
import numpy as np
import cv2
from PIL import Image
import pytesseract
from streamlit_drawable_canvas import st_canvas

st.set_page_config(page_title="SciReImage Pro Studio", layout="wide")

# --- CORE EXTRACTION ENGINE ---
@st.cache_data
def analyze_image(image_np, target_width=800):
    """Extracts text and shapes, scaling them to perfectly fit the Streamlit UI canvas."""
    
    # 1. Calculate Scaling Factors
    orig_h, orig_w = image_np.shape[:2]
    scale_factor = target_width / orig_w
    target_height = int(orig_h * scale_factor)
    
    canvas_objects = []

    # 2. Extract Text using Tesseract
    ocr_data = pytesseract.image_to_data(image_np, output_type=pytesseract.Output.DICT)
    
    for i in range(len(ocr_data['text'])):
        conf = int(ocr_data['conf'][i])
        text = ocr_data['text'][i].strip()
        
        if conf > 40 and text != "":
            # Apply scaling factor to coordinates and font size
            x = int(ocr_data['left'][i] * scale_factor)
            y = int(ocr_data['top'][i] * scale_factor)
            w = int(ocr_data['width'][i] * scale_factor)
            h = int(ocr_data['height'][i] * scale_factor)
            
            canvas_objects.append({
                "type": "text",
                "left": x + (w // 2), # fabric.js needs the center point
                "top": y + (h // 2),
                "text": text,
                "fontSize": max(12, int(h * 0.9)), # Prevent unreadably small text
                "fill": "#000000",
                "originX": "center",
                "originY": "center"
            })

    # 3. Extract Icons and Boxes using OpenCV
    gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
    # Threshold to find dark shapes on a light background
    _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        # Filter out tiny noise and massive background borders
        if 30 < w < (orig_w * 0.9) and 30 < h < (orig_h * 0.9):
            # Scale coordinates for the UI
            scaled_x = int(x * scale_factor)
            scaled_y = int(y * scale_factor)
            scaled_w = int(w * scale_factor)
            scaled_h = int(h * scale_factor)
            
            canvas_objects.append({
                "type": "rect",
                "left": scaled_x,
                "top": scaled_y,
                "width": scaled_w,
                "height": scaled_h,
                "fill": "rgba(0, 150, 255, 0.2)", # Transparent blue box over icons
                "stroke": "#0096FF",
                "strokeWidth": 2
            })

    return canvas_objects, target_height


# --- UI LAYOUT ---
st.title("🧬 SciReImage Pro Studio")
st.caption("Automated editing environment tailored for scientific media.")

col_sidebar, col_workspace = st.columns([1.5, 5])

with col_sidebar:
    st.header("📥 Input Hub")
    uploaded_file = st.file_uploader("Drop Figure or Slide", type=["png", "jpg", "jpeg"])
    
    if uploaded_file:
        if "bg_image" not in st.session_state or st.session_state.file_name != uploaded_file.name:
            # Load new image
            st.session_state.bg_image = Image.open(uploaded_file).convert("RGB")
            st.session_state.file_name = uploaded_file.name
            st.session_state.canvas_objects = []
            st.session_state.canvas_height = 600

    st.divider()
    tool_mode = st.radio("Active Engine Tool", ["Pointer/Select", "AI Eraser (Inpaint)"])
    
    if "bg_image" in st.session_state:
        if st.button("📝 Run Layout & Text Analysis"):
            with st.spinner("Extracting Text and Icons..."):
                img_np = np.array(st.session_state.bg_image)
                # Hardcoding UI width to 800 to match the canvas
                objects, scaled_height = analyze_image(img_np, target_width=800)
                st.session_state.canvas_objects = objects
                st.session_state.canvas_height = scaled_height
                st.rerun()

with col_workspace:
    st.subheader("🖥 Drawing Canvas")
    if "bg_image" in st.session_state:
        
        drawing_mode = "transform" if tool_mode == "Pointer/Select" else "freedraw"
        
        # We must resize the background image to exactly match the scaled coordinates
        # Otherwise, fabric.js misaligns the background and the drawn objects
        display_width = 800
        canvas_bg = st.session_state.bg_image.resize(
            (display_width, st.session_state.canvas_height), 
            Image.Resampling.LANCZOS
        )

        initial_drawing = {"objects": st.session_state.canvas_objects} if st.session_state.canvas_objects else None
        
        canvas_result = st_canvas(
            fill_color="rgba(255, 0, 0, 0.3)",
            stroke_width=3,
            stroke_color="#FF0000",
            background_image=canvas_bg,  # Use the perfectly scaled background
            drawing_mode=drawing_mode,
            initial_drawing=initial_drawing,
            update_streamlit=True,
            height=st.session_state.canvas_height,
            width=display_width,
            key="pro_studio_canvas"
        )
    else:
        st.info("Upload an image to activate the canvas workspace.")
