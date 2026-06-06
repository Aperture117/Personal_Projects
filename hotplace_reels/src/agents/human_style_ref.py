import logging
import json
import os
from src.services.ai_service import ai_service
from src.database.db_manager import db
from src.core.config import settings

logger = logging.getLogger(__name__)

class HumanStyleRefAgent:
    """
    Sub-Agent: Extracts 'Human Imperfection' patterns from top-performing posts.
    """
    async def analyze_viral_patterns(self, raw_posts: list):
        # 1. Check for User-Provided Few-Shots first
        few_shot_dir = "data/raw/few_shots"
        user_images = [os.path.join(few_shot_dir, f) for f in os.listdir(few_shot_dir) if f.endswith('.jpg')] if os.path.exists(few_shot_dir) else []
        
        if user_images:
            logger.info(f"🎯 Analyzing {len(user_images)} user-provided style masters...")
            target_image = user_images[-1]

            # Use Vision AI to extract the actual visual DNA of your photo
            style_dna = ai_service.analyze_visual_structure(target_image)

            pattern = {
                "id": "user_style_master",
                "text_informality": 0.9,
                "slang_used": ["~네여", "~함", "대박"],
                "emoji_strategy": "middle",
                "visual_vibe": style_dna.get("background", "High-end user aesthetic"),
                "layout_nodes": style_dna.get("layout_nodes", []),
                "color_palette": style_dna.get("color_palette", ["#000000", "#FFFFFF"]),
                "font_style": style_dna.get("font_style", "Bold Sans-serif"),
                # IMPORTANT: We do NOT pass reference_image back to be used as a background
                "style_guide_only": True 
            }
            return [pattern]

        logger.info(f"👁️ Analyzing {len(raw_posts)} viral posts for human-style DNA...")
        
        extracted_patterns = []
        for post in raw_posts:
            caption = post.get("source_caption", "")
            
            prompt = f"""
            Analyze the 'Human Style' of this viral Instagram post:
            Caption: "{caption}"
            
            Extract the following patterns in JSON format:
            1. 'text_informality': 0.0 to 1.0 (how messy/informal the text is)
            2. 'slang_used': List of informal words or slang
            3. 'typo_simulation': One or two common typos found or suggested
            4. 'emoji_strategy': How emojis are placed (middle, end, random)
            5. 'visual_vibe': Description of the photo style (e.g., 'shaky hand-held', 'natural sunlight', 'messy desk')
            
            Return ONLY valid JSON.
            """
            
            try:
                response = ai_service.client.generate(model=settings.LLM_MODEL, prompt=prompt, format="json")
                pattern = json.loads(response['response'])
                
                # Save to style_patterns table
                pattern_id = db.execute(
                    "INSERT INTO style_patterns (source_post_url, visual_pattern_json, text_pattern_json) VALUES (?, ?, ?)",
                    (post.get("url", ""), json.dumps(pattern.get("visual_vibe", {})), json.dumps(pattern))
                )
                
                pattern['id'] = pattern_id
                extracted_patterns.append(pattern)
            except Exception as e:
                logger.error(f"Failed to analyze style for post: {e}")
                
        return extracted_patterns

human_style_ref = HumanStyleRefAgent()
