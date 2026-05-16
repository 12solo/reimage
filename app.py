import streamlit as st
from PIL import Image
import numpy as np
from streamlit_drawable_canvas import st_canvas
import io

# Import modular backend (simulated for this architecture)
# from src.ai_vision import segment_image
# from src.ocr_engine import extract_editable_text
# from src.export_engine import export_to_pptx

st.set_page_config(page_title="SciReImage Pro Editor", layout="wide", initial_sidebar_state="expanded")

# --- Session State Management ---
if "layers" not in st.session_state:
    st.session_state.layers = []
if "bg_image" not in st.session_state:
    st.session_state.bg_image = None

# --- Top Navbar ---
st.markdown("""
    <style>
    .top-bar {background-color: #1E1E1E; padding: 10px; border-radius: 5px; color: white; display: flex; justify-content: space-between;}
    </style>
    <div class="top-bar">
        <h3>🧬 SciReImage Pro</h3>
        <p>AI-Powered Scientific Figure Editor</p>
    </div>
""", unsafe_allow_html=True)

# --- Layout: 3 Columns (Tools | Canvas | Layers & AI) ---
col_tools, col_canvas, col_ai = st.columns([1, 4, 1.5])

# --- 1. TOOLBAR (Left) ---
with col_tools:
    st.subheader("🛠 Tools")
    uploaded_file = st.file_uploader("Upload Image", type=["png", "jpg", "pdf", "svg"])
    
    if uploaded_file:
        if st.session_state.bg_image is None:
            st.session_state.bg_image = Image.open(uploaded_file).convert("RGB")
            
    st.divider()
    active_tool = st.radio("Mode", ["Select", "AI Magic Brush", "Text Edit", "Inpaint Erase"])
    
    st.divider()
    st.button("⛶ Auto-Segment Image (SAM)", help="Uses Segment Anything to break image into layers")
    st.button("📝 Extract Scientific Text", help="Uses PaddleOCR + Mathpix")

# --- 2. MAIN CANVAS (Center) ---
with col_canvas:
    st.write("### Workspace")
    if st.session_state.bg_image:
        canvas_mode = "transform" if active_tool == "Select" else "freedraw"
        
        # The main interactive fabric.js canvas
        canvas_result = st_canvas(
            fill_color="rgba(255, 0, 0, 0.3)",
            stroke_width=3,
            stroke_color="#FF0000",
            background_image=st.session_state.bg_image,
            update_streamlit=True,
            height=600,
            width=800,
            drawing_mode=canvas_mode,
            key="main_canvas",
        )
    else:
        st.info("Upload an image or diagram to start the workspace.")

# --- 3. LAYERS & AI ASSISTANT (Right) ---
with col_ai:
    # Layers Panel
    st.subheader("📑 Layers")
    with st.expander("Background (Original)", expanded=True):
        st.write("👁️ Visible | 🔒 Locked")
    
    # Simulate dynamically added layers
    if len(st.session_state.layers) > 0:
        for i, layer in enumerate(st.session_state.layers):
            with st.expander(f"Layer {i+1}: {layer['name']}"):
                st.write("👁️ Visible")
                st.button(f"Delete Layer {i}", key=f"del_{i}")
    else:
        st.caption("Run Auto-Segment to generate editable layers.")

    st.divider()
    
    # AI NLP Editing Prompt
    st.subheader("🤖 AI Assistant")
    nlp_command = st.text_input("Tell AI what to do...")
    if st.button("Execute AI Action"):
        if "make arrows blue" in nlp_command.lower():
            st.success("AI is using GroundingDINO to find arrows, and recoloring them blue!")
        elif "replace" in nlp_command.lower():
            st.success("AI is isolating object and generating replacement via Stable Diffusion...")
            
    st.divider()
    
    # Export Engine
    st.subheader("💾 Export")
    export_format = st.selectbox("Format", ["SVG (Vector)", "PPTX (PowerPoint)", "Draw.io", "High-Res PNG"])
    st.button("Generate Download", type="primary")
