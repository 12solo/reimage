from pptx import Presentation
from pptx.util import Inches
import svgwrite

def convert_layers_to_pptx(bg_image, layers_data):
    """
    Takes the reconstructed background and extracted OCR text layers 
    and packages them as editable text boxes inside a real PowerPoint file.
    """
    prs = Presentation()
    blank_slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_slide_layout)
    
    # Add background
    # slide.shapes.add_picture("temp_bg.png", 0, 0, width=prs.slide_width)
    
    # Add editable text boxes
    for layer in layers_data:
        if layer["type"] == "text":
            txBox = slide.shapes.add_textbox(Inches(layer["x"]), Inches(layer["y"]), Inches(layer["w"]), Inches(layer["h"]))
            tf = txBox.text_frame
            tf.text = layer["text"]
            
    prs.save("output_presentation.pptx")
    return "output_presentation.pptx"
