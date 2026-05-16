import pytesseract
import numpy as np

class ScientificOCREngine:
    def __init__(self):
        # We are bypassing PaddleOCR and using the much more stable Tesseract engine
        self.engine_name = "Tesseract"

    def extract_text_layers(self, image_np):
        """
        Scans the image using PyTesseract and returns a list of dictionaries 
        formatting the text as editable layers for the Streamlit canvas.
        """
        # Run Tesseract to get text, bounding boxes, and confidence scores
        data = pytesseract.image_to_data(image_np, output_type=pytesseract.Output.DICT)
        
        text_layers = []
        
        for i in range(len(data['text'])):
            conf = int(data['conf'][i])
            text = data['text'][i].strip()
            
            # Filter out noise: empty text or very low confidence predictions (< 40)
            if conf > 40 and text != "":
                x = data['left'][i]
                y = data['top'][i]
                w = data['width'][i]
                h = data['height'][i]
                
                # Create a layer object compatible with Fabric.js (st_canvas)
                text_layers.append({
                    "id": f"text_{i}",
                    "name": f"Text: {text[:10]}...",
                    "type": "text",
                    "text": text,
                    "confidence": float(conf) / 100.0,
                    "bbox": {"x": x, "y": y, "w": w, "h": h},
                    "font_size": int(h * 0.8), # Estimate font size from bounding box
                    "color": "#000000"
                })
                
        return text_layers
