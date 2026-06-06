import logging
import os
import json
from src.services.feed_creator import feed_creator
from src.services.imperfection_modifier import human_touch, humanizer
from src.database.db_manager import db
from src.services.naver_service import NaverService
from src.services.media_downloader import media_downloader
from PIL import Image

logger = logging.getLogger(__name__)

class RenderAgent:
    """
    Sub-Agent: Renders NEW assets of NEW places, but in the Viral/User Style.
    """
    def __init__(self):
        self.naver = NaverService()

    async def render_imperfect_asset(self, draft: dict, style_dna: dict):
        logger.info(f"✨ RenderAgent: Finalizing asset for draft {draft.get('id')}...")

        # 1. Humanize Text
        draft['hook'] = humanizer.transform(draft['hook'])
        draft['body'] = humanizer.transform(draft['body'])

        # 2. Fetch NEW Backgrounds for the NEW topic (Don't reuse user's few-shot!)
        # Use the niche/topic from the draft or style_dna
        topic = draft.get("niche") or style_dna.get("visual_vibe", "Seoul Aesthetic")
        logger.info(f"📸 Fetching original backgrounds for topic: {topic}")
        
        image_urls = self.naver.search_images(topic, display=5)
        new_base_images = media_downloader.download_images(topic, image_urls)

        # 3. Base Rendering using Style DNA (Layout & Font)
        # We extract positions and colors from the user-provided style_dna
        layout_nodes = style_dna.get('layout_nodes', [{'position': 'center', 'size': 'large'}])
        primary_pos = layout_nodes[0].get('position', 'center') if layout_nodes else 'center'

        slides_data = [
            {
                "layout_nodes": [{"type": "text", "content": draft['hook'], "position": primary_pos, "size": "large"}], 
                "color_palette": style_dna.get("color_palette", ["#000000", "#FFFFFF"]),
                "font_style": style_dna.get("font_style", "Bold Sans-serif")
            },
            {
                "layout_nodes": [{"type": "text", "content": draft['body'], "position": "bottom", "size": "small"}], 
                "color_palette": style_dna.get("color_palette", ["#000000", "#FFFFFF"]),
                "font_style": style_dna.get("font_style", "Bold Sans-serif")
            }
        ]

        # Render using the FRESH images of the NEW topic
        output_paths = feed_creator.create_carousel(f"batch_{draft['id']}", slides_data, base_images=new_base_images)

        # 4. Apply Imperfection FX to each slide
        final_paths = []
        applied_fx = ["Noise", "ColorShift", "MicroBlur"]
        
        for path in output_paths:
            img = Image.open(path)
            img = human_touch.add_noise(img)
            img = human_touch.shift_colors(img)
            img = human_touch.micro_blur(img)
            
            final_path = path.replace(".png", "_imperfect.png")
            img.save(final_path)
            final_paths.append(final_path)
            
            # Save to render_assets table
            db.execute(
                "INSERT INTO render_assets (draft_id, file_path, imperfection_metadata) VALUES (?, ?, ?)",
                (draft['id'], final_path, json.dumps(applied_fx))
            )
            
        return final_paths

render_agent = RenderAgent()
