import os
from PIL import Image, ImageDraw, ImageFont
import logging
from src.core.config import settings

logger = logging.getLogger(__name__)

class FeedCreator:
    def __init__(self, output_dir: str = "data_storage/feeds"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.size = (1080, 1080) # Instagram Square

    def _get_font(self, style: str, size: int):
        # Try to find a valid Korean font on Windows
        possible_fonts = [
            "C:/Windows/Fonts/malgunbd.ttf", # Malgun Gothic Bold
            "C:/Windows/Fonts/malgun.ttf",   # Malgun Gothic
            "C:/Windows/Fonts/arial.ttf"     # Fallback
        ]
        for font_path in possible_fonts:
            if os.path.exists(font_path):
                try:
                    return ImageFont.truetype(font_path, size)
                except:
                    continue
        return ImageFont.load_default()

    def _add_professional_effects(self, img):
        """Adds gradients and aesthetic overlays."""
        overlay = Image.new('RGBA', self.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Bottom-up dark gradient for text readability
        for i in range(self.size[1]//2, self.size[1]):
            alpha = int((i - self.size[1]//2) / (self.size[1]//2) * 160)
            draw.line([(0, i), (self.size[0], i)], fill=(0, 0, 0, alpha))
            
        return Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')

    def _draw_glass_card(self, draw, box_coords, color=(255, 255, 255, 120)):
        """Draws a modern semi-transparent 'glass' card behind text."""
        overlay = Image.new('RGBA', self.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(overlay)
        d.rounded_rectangle(box_coords, radius=20, fill=color)
        return overlay

    def _smart_crop(self, img):
        aspect_ratio = img.width / img.height
        target_ratio = self.size[0] / self.size[1]
        if aspect_ratio > target_ratio:
            new_width = int(self.size[1] * aspect_ratio)
            img = img.resize((new_width, self.size[1]), Image.Resampling.LANCZOS)
            left = (img.width - self.size[0]) / 2
            img = img.crop((left, 0, left + self.size[0], self.size[1]))
        else:
            new_height = int(self.size[0] / aspect_ratio)
            img = img.resize((self.size[0], new_height), Image.Resampling.LANCZOS)
            top = (img.height - self.size[1]) / 2
            img = img.crop((0, top, self.size[0], top + self.size[1]))
        return img

    def replicate_slide(self, background_path: str, layout: dict, output_path: str, place_info: dict = None):
        """
        Creates a high-end designer-grade slide.
        """
        try:
            # 1. Background Setup
            if background_path and os.path.exists(background_path):
                img = Image.open(background_path).convert('RGB')
            else:
                img = Image.new('RGB', self.size, color="#1A1A1A")
            
            # Smart Center-Crop
            img = self._smart_crop(img)
            img = self._add_professional_effects(img)
            
            # Base Layer
            base = img.convert('RGBA')
            txt_layer = Image.new('RGBA', self.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(txt_layer)

            # 2. Advanced Layout Rendering
            for node in layout.get('layout_nodes', []):
                if node['type'] == 'text':
                    text = node.get('content', '')
                    pos_type = node.get('position', 'center')
                    is_title = node.get('size') == 'large'
                    
                    font = self._get_font("Bold Sans-serif", 85 if is_title else 40)
                    
                    # Wrap text
                    import textwrap
                    wrapped_text = "\n".join(textwrap.wrap(text, width=12 if is_title else 25))
                    
                    bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font, align="center")
                    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
                    
                    # Calculate Position
                    if pos_type == 'top': pos = ((self.size[0]-w)/2, 180)
                    elif pos_type == 'bottom': pos = ((self.size[0]-w)/2, self.size[1]-h-200)
                    else: pos = ((self.size[0]-w)/2, (self.size[1]-h)/2 + 100)

                    # 3. Glassmorphism Card
                    if not is_title:
                        card_box = [pos[0]-30, pos[1]-20, pos[0]+w+30, pos[1]+h+20]
                        glass = self._draw_glass_card(draw, card_box)
                        base = Image.alpha_composite(base, glass)

                    # 4. Draw Text with Drop Shadow
                    draw.multiline_text((pos[0]+3, pos[1]+3), wrapped_text, font=font, fill=(0,0,0,100), align="center")
                    draw.multiline_text(pos, wrapped_text, font=font, fill="white", align="center")

            # 5. Final Composition
            final = Image.alpha_composite(base, txt_layer).convert('RGB')
            final.save(output_path, "PNG", quality=95)
            return output_path
        except Exception as e:
            logger.error(f"Professional Render Error: {e}")
            return None

    def create_carousel(self, place_name: str, slides_data: list, base_images: list[str] = None):
        """
        Creates a set of carousel images based on a list of slide layouts.
        """
        logger.info(f"📸 Creating Replicated Instagram Carousel for: {place_name}")
        saved_paths = []
        place_slug = place_name.replace(" ", "_")
        
        for i, slide in enumerate(slides_data):
            bg_path = base_images[i] if base_images and i < len(base_images) else None
            output_path = os.path.join(self.output_dir, f"{place_slug}_slide_{i}.png")
            
            result = self.replicate_slide(bg_path, slide, output_path)
            if result:
                saved_paths.append(result)

        return saved_paths

feed_creator = FeedCreator()
