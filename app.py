import streamlit as st
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import pytesseract
from pdf2image import convert_from_bytes
from streamlit_drawable_canvas import st_canvas
import io
import json

st.set_page_config(page_title="High-Res Diagram Editor", layout="wide")

# --- Helper Functions ---

def get_pytesseract_data(pil_image):
    """Extracts text and bounding boxes from a PIL image."""
    data = pytesseract.image_to_data(pil_image, output_type=pytesseract.Output.DICT)
    parsed_objects = []
    
    for i in range(len(data['text'])):
        # Filter out noise (low confidence or empty text)
        if int(data['conf'][i]) > 50 and data['text'][i].strip() != "":
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            parsed_objects.append({
                "text": data['text'][i],
                "left": x,
                "top": y,
                "width": w,
                "height": h
            })
    return parsed_objects

def scale_ocr_to_canvas(ocr_data, scale_factor_x, scale_factor_y):
    """Scales full-res OCR coordinates down to fit the display canvas."""
    canvas_objects = []
    for obj in ocr_data:
        canvas_objects.append({
            "type": "text",
            # We want to provide the *center* of the object to st_canvas
            "left": int((obj["left"] + (obj["width"] / 2)) * scale_factor_x),
            "top": int((obj["top"] + (obj["height"] / 2)) * scale_factor_y),
            "text": obj["text"],
            "fill": "#00FF00", # Initial Green color for OCR visibility
            "fontSize": 20, # Initial small size for canvas
            "originX": "center",
            "originY": "center"
        })
    return canvas_objects

def save_high_res(original_pil_image, canvas_json_data, canvas_width, canvas_height):
    """Applies browser canvas edits back to the full-res original image."""
    
    # 1. Start with the original high-resolution image
    output_image = original_pil_image.copy().convert("RGBA")
    draw = ImageDraw.Draw(output_image)
    
    # 2. Calculate Scaling Factors (Canvas -> Original)
    orig_w, orig_h = original_pil_image.size
    scale_x = orig_w / canvas_width
    scale_y = orig_h / canvas_height
    
    # 3. Load a default font (You might need to provide a path to a proper .ttf file for perfect results)
    try:
        font_default = ImageFont.load_default()
    except:
        # Fallback if no font system works
        font_default = None

    # 4. Iterate through every object edited on the front-end
    if "objects" in canvas_json_data:
        for obj in canvas_json_data["objects"]:
            if obj["type"] == "text":
                # Get front-end properties
                text_content = obj["text"]
                
                # Scale front-end coordinates back to full-res
                # Fabric.js (st_canvas) uses object center; Pillow uses top-left corner.
                obj_orig_center_x = obj["left"] * scale_x
                obj_orig_center_y = obj["top"] * scale_y
                obj_scaled_width = obj["width"] * obj["scaleX"] * scale_x
                obj_scaled_height = obj["height"] * obj["scaleY"] * scale_y
                
                corner_x = obj_orig_center_x - (obj_scaled_width / 2)
                corner_y = obj_orig_center_y - (obj_scaled_height / 2)
                
                # Scale Font Size
                final_font_size = int(obj["fontSize"] * obj["scaleX"] * scale_x)
                
                # Update Font with scaled size
                if final_font_size > 0:
                    try:
                        # Attempt to load a real font if available, fallback to default scaled
                        font = ImageFont.truetype("Arial.ttf", final_font_size)
                    except:
                        font = font_default # Pillow can't scale default font well

                # Extract Color (assuming hex, e.g., #FF0000FF)
                fill_color = obj["fill"]
                
                # 5. Draw the text onto the full-resolution image
                draw.text((corner_x, corner_y), text_content, font=font, fill=fill_color)
                
    return output_image.convert("RGB") # Remove alpha channel for saving as JPEG/PNG

# --- UI Setup ---
st.title("🖌️ Scientific Diagram & Photo Editor (High-Res)")
st.markdown("""
Upload a static image (flowchart, scan, figure). We'll convert the text into editable boxes. 
Drag them, change the words, resize them, and download the full-resolution result.
""")

# Setup Sidebar
with st.sidebar:
    st.header("1. Upload & Settings")
    uploaded_file = st.file_uploader("Upload Image/PDF", type=['png', 'jpg', 'jpeg', 'pdf'])
    
    canvas_width = st.slider("Display Canvas Width (Does not affect output resolution)", 400, 1600, 1000)
    
    st.markdown("---")
    st.header("How to Edit:")
    st.markdown("""
    *   **Select:** Click an object.
    *   **Move:** Drag selected object.
    *   **Edit Text:** Double-click the green text box on the canvas.
    *   **Resize:** Drag the corners of the selection box.
    *   **Change Color/Size:** Use the object properties menu that appears on the canvas.
    """)

# --- Main App Logic ---

if uploaded_file:
    # 1. Load Original Image (Full Resolution)
    if uploaded_file.name.lower().endswith('.pdf'):
        # For simplicity in this example, only process page 1 of PDFs
        pages = convert_from_bytes(uploaded_file.read(), first_page=1, last_page=1)
        original_image = pages[0]
    else:
        original_image = Image.open(uploaded_file).convert('RGB')

    orig_w, orig_h = original_image.size
    
    # 2. Run OCR (Once per upload)
    # We store the OCR data in st.session_state so it doesn't re-run every rerun.
    state_key_ocr = f"ocr_data_{uploaded_file.name}"
    if state_key_ocr not in st.session_state:
        with st.spinner("Analyzing diagram layout..."):
            raw_ocr_data = get_pytesseract_data(original_image)
            st.session_state[state_key_ocr] = raw_ocr_data
    
    ocr_data = st.session_state[state_key_ocr]

    # 3. Handle Scaling for the Canvas Display
    # We display a scaled version (e.g., 1000px wide) for performance in the browser.
    display_scale_x = canvas_width / orig_w
    canvas_height = int(orig_h * display_scale_x)
    
    # 4. Prepare initial canvas objects from scaled OCR
    initial_drawing = {"objects": scale_ocr_to_canvas(ocr_data, display_scale_x, display_scale_x)}

    # 5. The Interactive Canvas component
    st.subheader("2. Interactive Editor Canvas")
    
    # We must use a unique key for the canvas based on the file name
    canvas_result = st_canvas(
        fill_color="rgba(0, 255, 0, 0.2)",  # Fill color for new drawings
        stroke_width=2,
        stroke_color="#00FF00",
        background_image=original_image, # Streamlit automatically scales the background_image to fit width/height
        update_streamlit=True,
        width=canvas_width,
        height=canvas_height,
        drawing_mode="transform", # "transform" allows selecting/moving existing objects
        initial_drawing=initial_drawing,
        key=f"canvas_{uploaded_file.name}",
    )

    # 6. Handle Saving and Downloading
    st.markdown("---")
    st.subheader("3. Save Full-Resolution Result")
    
    if canvas_result.json_data is not None:
        # We give the user a button to trigger the high-res rendering, 
        # as it can be slow for large images.
        if st.button("Generate High-Resolution Edited Image"):
            with st.spinner("Applying edits to original high-res file..."):
                
                # Perform the backend rendering
                final_image = save_high_res(
                    original_image, 
                    canvas_result.json_data, 
                    canvas_width, 
                    canvas_height
                )
                
                # Display processed preview (scaled for UI)
                st.image(final_image, caption="High-Res Output Preview", use_container_width=True)
                
                # Prepare download buffer
                img_buffer = io.BytesIO()
                final_image.save(img_buffer, format="PNG")
                processed_bytes = img_buffer.getvalue()
                
                st.download_button(
                    label=f"Download Edited Image ({orig_w}x{orig_h})",
                    data=processed_bytes,
                    file_name=f"edited_{uploaded_file.name}.png",
                    mime="image/png"
                )

else:
    st.info("👈 Please upload an image in the sidebar to begin.")
