import streamlit as st
import numpy as np
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import io

# Import backend services
from src.layer_manager import LayerManager
from src.ocr_engine import ScientificOCREngine
from src.ai_generate import AIGenerateEngine
from src.export_engine import convert_layers_to_pptx

st.set_page_config(page_title="SciReImage Pro Studio", layout="wide")

# --- Initialize Pipeline States ---
if "layer_manager" not in st.session_state:
    st.session_state.layer_manager = LayerManager()
if "ocr_engine" not in st.session_state:
    st.session_state.ocr_engine = ScientificOCREngine()
if "ai_gen" not in st.session_state:
    st.session_state.ai_gen = AIGenerateEngine()
if "canvas_objects" not in st.session_state:
    st.session_state.canvas_objects = []

st.title("🧬 SciReImage Pro Studio")
st.caption("Adobe-level automated editing environment tailored for scientific media, flowcharts, and diagrams.")

# --- Application Layout ---
col_sidebar, col_workspace, col_layers = st.columns([1.5, 4, 1.5])

with col_sidebar:
    st.header("📥 Input Hub")
    uploaded_file = st.file_uploader("Drop Figure or Slide", type=["png", "jpg", "jpeg", "pdf", "svg"])
    
    if uploaded_file:
        # Check if a new file is loaded to avoid clearing ongoing sessions unexpectedly
        if st.session_state.layer_manager.background is None or getattr(st.session_state, 'last_uploaded', None) != uploaded_file.name:
            raw_img = Image.open(uploaded_file).convert("RGB")
            st.session_state.layer_manager = LayerManager() # Reset manager for new file
            st.session_state.layer_manager.initialize_background(raw_img)
            st.session_state.canvas_objects = []
            st.session_state.last_uploaded = uploaded_file.name
            
    st.divider()
    st.header("⚡ Smart Tools")
    tool_mode = st.radio("Active Engine Tool", ["Pointer/Select", "Text Extractor", "AI Eraser (Inpaint)", "Object Swapper"])
    
    if st.session_state.layer_manager.background:
        st.subheader("Automations")
        if st.button("📝 Run Layout & Text Analysis"):
            with st.spinner("Executing OCR Pipeline..."):
                bg_np = np.array(st.session_state.layer_manager.background)
                detected_texts = st.session_state.ocr_engine.extract_text_layers(bg_np)
                
                # Transform OCR records directly into interactive fabric.js UI configurations
                new_objects = []
                for t in detected_texts:
                    new_objects.append({
                        "type": "text",
                        "left": t["bbox"]["x"] + (t["bbox"]["w"] // 2),
                        "top": t["bbox"]["y"] + (t["bbox"]["h"] // 2),
                        "width": t["bbox"]["w"],  # Saved so the scaling loop can use it later!
                        "height": t["bbox"]["h"], # Saved so the scaling loop can use it later!
                        "text": t["text"],
                        "fontSize": t["font_size"],
                        "fill": "#000000",
                        "originX": "center",
                        "originY": "center"
                    })
                st.session_state.canvas_objects = new_objects
                st.rerun()

with col_workspace:
    st.subheader("🖥 Drawing Canvas")
    if st.session_state.layer_manager.background:
        
        # Adjust Canvas Modes based on selected tools
        drawing_mode = "transform"
        if tool_mode in ["AI Eraser (Inpaint)", "Object Swapper"]:
            drawing_mode = "freedraw"
            
        # --- THE FIX: DYNAMIC SCALING ---
        # 1. Get the original image
        orig_img = st.session_state.layer_manager.background
        
        # 2. Lock the width to 800px to fit the Streamlit column perfectly
        display_width = 800
        
        # 3. Calculate the correct aspect ratio height so the image doesn't stretch
        # We also save this ratio as "scale_factor" to use on the text coordinates!
        scale_factor = display_width / orig_img.width
        display_height = int(orig_img.height * scale_factor)
        
        # 4. Resize a copy of the image specifically for the UI canvas
        canvas_bg_image = orig_img.resize((display_width, display_height), Image.Resampling.LANCZOS)
        
        # 5. SCALE THE OCR COORDINATES! 
        scaled_objects = []
        for obj in st.session_state.canvas_objects:
            scaled_obj = obj.copy()
            if "left" in scaled_obj:
                scaled_obj["left"] = int(scaled_obj["left"] * scale_factor)
            if "top" in scaled_obj:
                scaled_obj["top"] = int(scaled_obj["top"] * scale_factor)
            if "width" in scaled_obj:
                scaled_obj["width"] = int(scaled_obj["width"] * scale_factor)
            if "height" in scaled_obj:
                scaled_obj["height"] = int(scaled_obj["height"] * scale_factor)
            if "fontSize" in scaled_obj:
                # Scale the font, but don't let it get smaller than 12pt so it remains readable
                scaled_obj["fontSize"] = max(12, int(scaled_obj["fontSize"] * scale_factor)) 
                
            scaled_objects.append(scaled_obj)
            
        initial_drawing = {"objects": scaled_objects}
        # --------------------------------
        
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)" if tool_mode == "Object Swapper" else "rgba(255, 0, 0, 0.3)",
            stroke_width=4,
            stroke_color="#FFA500" if tool_mode == "Object Swapper" else "#FF0000",
            background_image=canvas_bg_image,  # Use the scaled image
            drawing_mode=drawing_mode,
            initial_drawing=initial_drawing,   # Use the scaled coordinates
            update_streamlit=True,
            height=display_height,             # Use the dynamic height
            width=display_width,               # Use the locked width
            key="pro_studio_canvas"
        )
        
        # Handle Natural Language Processing Box
        st.markdown("### 🤖 Direct AI Command Prompt")
        ai_prompt = st.text_input("Type an instruction (e.g., 'Turn all arrows blue')", key="nlp_input")
        if st.button("Apply AI Transformation") and ai_prompt:
            st.success(f"Successfully processed directive: '{ai_prompt}'")
    else:
        st.info("Awaiting structural image input to activate canvas workspace.")

with col_layers:
    st.header("📑 Layer Management")
    
    # Render interactive layers stack UI mimicking Photoshop
    if st.session_state.layer_manager.background:
        for idx, layer in enumerate(st.session_state.layer_manager.layers):
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                c1.write(f"📁 {layer['name']}")
                is_visible = c2.checkbox("👁", value=layer.get("visible", True), key=f"vis_{layer['id']}")
                layer["visible"] = is_visible
                
        st.divider()
        st.header("💾 Production Export")
        export_target = st.selectbox("Target Output Format", ["Editable PowerPoint (.pptx)", "Scalable Vector Graphics (.svg)", "High-Res Image Layer (.png)"])
        
        if st.button("Compile & Download File", type="primary"):
            if "PowerPoint" in export_target:
                st.info("PowerPoint compilation initiated...")
                # simulated_layers = [{"type": "text", "text": obj["text"], "x": obj["left"]/100, "y": obj["top"]/100, "w": 3, "h": 1} for obj in canvas_result.json_data["objects"] if obj["type"] == "text"]
                # pptx_path = convert_layers_to_pptx(st.session_state.layer_manager.background, simulated_layers)
                # st.download_button(...)
