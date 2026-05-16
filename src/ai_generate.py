import torch
from PIL import Image, ImageOps
import numpy as np

try:
    from diffusers import StableDiffusionInpaintPipeline
    DIFFUSERS_AVAILABLE = True
except ImportError:
    DIFFUSERS_AVAILABLE = False

class AIGenerateEngine:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.inpaint_pipe = None

    def load_models(self):
        """Lazy loads the Stable Diffusion Inpainting pipeline onto the GPU."""
        if DIFFUSERS_AVAILABLE and self.inpaint_pipe is None:
            # Using a highly-optimized, fast inpainting model
            self.inpaint_pipe = StableDiffusionInpaintPipeline.from_pretrained(
                "runwayml/stable-diffusion-inpainting",
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
            )
            self.inpaint_pipe.to(self.device)
            # Enable memory optimizations if on a local GPU
            if self.device == "cuda":
                self.inpaint_pipe.enable_attention_slicing()

    def remove_object_and_heal(self, original_image, mask_image):
        """
        Erases an object under the mask and seamlessly fills the background 
        by prompting the AI to interpret the surrounding context.
        """
        self.load_models()
        if not DIFFUSERS_AVAILABLE:
            raise RuntimeError("Diffusers/Torch stack not available in current environment.")
            
        # Ensure images are properly sized and matched
        orig_w, orig_h = original_image.size
        # Stable Diffusion works best with multiples of 8 (or 512x512 / 768x768)
        img_resized = original_image.resize((512, 512))
        mask_resized = mask_image.resize((512, 512))
        
        # Run inpainting with an empty or background-matching text prompt
        prompt = "clean scientific background, high resolution, matching texture, seamless"
        
        with torch.inference_mode():
            result = self.inpaint_pipe(
                prompt=prompt, 
                image=img_resized, 
                mask_image=mask_resized,
                negative_prompt="text, logo, blurry, artifacts, deformed objects"
            ).images[0]
            
        return result.resize((orig_w, orig_h))

    def replace_object_with_prompt(self, original_image, mask_image, prompt_text):
        """
        Replaces the object inside the mask with a completely new object 
        described by the user's natural language input.
        """
        self.load_models()
        if not DIFFUSERS_AVAILABLE:
            return original_image
            
        orig_w, orig_h = original_image.size
        img_resized = original_image.resize((512, 512))
        mask_resized = mask_image.resize((512, 512))
        
        full_prompt = f"{prompt_text}, clean vector graphic icon, scientific journal style, crisp publication quality"
        
        with torch.inference_mode():
            result = self.inpaint_pipe(
                prompt=full_prompt,
                image=img_resized,
                mask_image=mask_resized,
                negative_prompt="blurry, photorealistic, cluttered, messy background, low quality"
            ).images[0]
            
        return result.resize((orig_w, orig_h))
