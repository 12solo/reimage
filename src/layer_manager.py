import cv2
import numpy as np
from PIL import Image

class LayerManager:
    def __init__(self):
        self.layers = []
        self.background = None

    def initialize_background(self, image_pil):
        """Sets the base layer from which objects will be extracted."""
        self.background = image_pil
        self.layers.append({
            "id": "bg_0",
            "name": "Background",
            "type": "image",
            "visible": True,
            "locked": True,
            "content": image_pil,
            "z_index": 0
        })

    def create_layer_from_mask(self, mask_np, original_image_np, label="Extracted Object"):
        """
        Takes a binary mask from Segment Anything (SAM) and creates a transparent 
        PNG layer containing only that isolated object.
        """
        # 1. Apply mask to the original image to isolate the object
        rgba_image = cv2.cvtColor(original_image_np, cv2.COLOR_RGB2RGBA)
        rgba_image[:, :, 3] = mask_np * 255 # Set alpha channel based on mask
        
        # 2. Find bounding box to crop the layer tightly around the object
        coords = cv2.findNonZero((mask_np * 255).astype(np.uint8))
        if coords is not None:
            x, y, w, h = cv2.boundingRect(coords)
            cropped_object = rgba_image[y:y+h, x:x+w]
            
            # 3. Store as a new movable layer
            new_layer = {
                "id": f"layer_{len(self.layers)}",
                "name": f"{label} {len(self.layers)}",
                "type": "vector_object",
                "visible": True,
                "locked": False,
                "content": Image.fromarray(cropped_object),
                "bbox": {"x": x, "y": y, "w": w, "h": h},
                "z_index": len(self.layers)
            }
            self.layers.append(new_layer)
            return new_layer
        return None

    def remove_layer(self, layer_id):
        self.layers = [layer for layer in self.layers if layer["id"] != layer_id]

    def get_flattened_image(self):
        """Composites all visible layers back together for exporting."""
        if not self.background:
            return None
            
        base = self.background.copy().convert("RGBA")
        
        # Sort layers by z-index to ensure correct stacking
        sorted_layers = sorted(self.layers[1:], key=lambda k: k['z_index'])
        
        for layer in sorted_layers:
            if layer["visible"] and layer["type"] != "text":
                # Paste the object onto the background using its alpha channel as a mask
                bbox = layer["bbox"]
                base.paste(layer["content"], (bbox["x"], bbox["y"]), layer["content"])
                
        return base.convert("RGB")
