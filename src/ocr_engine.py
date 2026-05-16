import numpy as np
try:
    from paddleocr import PaddleOCR
    PADDLE_AVAILABLE = True
except ImportError:
    PADDLE_AVAILABLE = False

class ScientificOCREngine:
    def __init__(self):
        if PADDLE_AVAILABLE:
            # Enable English and specific models trained on mathematical/scientific structures
            self.ocr = PaddleOCR(use_angle_cls=True, lang='en')
        else:
            self.ocr = None

    def extract_text_layers(self, image_np):
        """
        Scans the image and returns a list of dictionaries formatting the text 
        as editable layers for the Streamlit canvas.
        """
        if not self.ocr:
            raise RuntimeError("PaddleOCR is not installed. GPU environment required.")

        results = self.ocr.ocr(image_np, cls=True)
        text_layers = []
        
        if results and results[0]:
            for idx, line in enumerate(results[0]):
                box = line[0]     # Polygon coordinates
                text = line[1][0] # The actual text string
                conf = line[1][1] # Confidence score
                
                # Convert polygon to standard X, Y, Width, Height
                x_coords = [point[0] for point in box]
                y_coords = [point[1] for point in box]
                x, y = min(x_coords), min(y_coords)
                w, h = max(x_coords) - x, max(y_coords) - y
                
                # Create a layer object compatible with Fabric.js (st_canvas)
                text_layers.append({
                    "id": f"text_{idx}",
                    "name": f"Text: {text[:10]}...",
                    "type": "text",
                    "text": text,
                    "confidence": conf,
                    "bbox": {"x": int(x), "y": int(y), "w": int(w), "h": int(h)},
                    "font_size": int(h * 0.8), # Estimate font size based on bounding box height
                    "color": "#000000"
                })
                
        return text_layers
