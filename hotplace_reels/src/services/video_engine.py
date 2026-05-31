from moviepy import ImageClip, TextClip, CompositeVideoClip, concatenate_videoclips, ColorClip
import os
import logging
from src.core.config import settings

logger = logging.getLogger(__name__)

class ReelsVideoCreator:
    def __init__(self, output_dir: str = "data_storage/reels"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.size = (1080, 1920) # 9:16 Vertical

    def create_video(self, place_name: str, script: str, image_paths: list[str] = None):
        """
        Creates a high-quality Reels video with zoom effects and better typography.
        """
        logger.info(f"🎬 Rendering Pro-quality Reels for: {place_name}")
        
        # Extract meaningful lines
        lines = [line.strip() for line in script.split('\n') if line.strip() and len(line) > 10][:5]
        
        clips = []
        
        for i, line in enumerate(lines):
            # 1. Background Image with Ken Burns Effect (Zoom)
            if image_paths and i < len(image_paths):
                try:
                    img_clip = ImageClip(image_paths[i]).with_duration(3.5).resized(height=self.size[1])
                    
                    # Apply a slow zoom-in effect to make it feel like video
                    def zoom(t):
                        return 1 + 0.05 * t  # Zoom in 5% over the duration
                    
                    bg_clip = img_clip.resized(zoom).cropped(
                        x_center=self.size[0]/2, y_center=self.size[1]/2,
                        width=self.size[0], height=self.size[1]
                    )
                except Exception as e:
                    logger.warning(f"Image processing failed, fallback to color: {e}")
                    bg_clip = ColorClip(size=self.size, color=(20, 20, 20)).with_duration(3.5)
            else:
                bg_clip = ColorClip(size=self.size, color=(20, 20, 20)).with_duration(3.5)

            # 2. Trendy Typography (Text with semi-transparent background box)
            try:
                # Create the text
                txt = TextClip(
                    text=line, 
                    font_size=55, 
                    color='white', 
                    size=(self.size[0]*0.85, None), 
                    method='caption',
                    text_align='center'
                ).with_duration(3.5)
                
                # Create a black semi-transparent box behind text for readability
                box_width = txt.w + 40
                box_height = txt.h + 40
                text_bg = ColorClip(size=(box_width, box_height), color=(0,0,0)).with_opacity(0.6).with_duration(3.5)
                
                # Composite text over the box
                styled_text = CompositeVideoClip([text_bg, txt.with_position('center')])
                styled_text = styled_text.with_position(('center', 1400)) # Position near bottom
                
                # Final segment: Image + Styled Text
                video_segment = CompositeVideoClip([bg_clip, styled_text])
            except Exception as e:
                logger.error(f"Text rendering failed: {e}")
                video_segment = bg_clip
                
            clips.append(video_segment)

        if not clips:
            return None

        # 3. Concatenate with smooth crossfade
        final_video = concatenate_videoclips(clips, method="compose")
        
        output_path = os.path.join(self.output_dir, f"{place_name.replace(' ', '_')}_vpro.mp4")
        
        # 4. Final Render
        final_video.write_videofile(output_path, fps=24, codec="libx264", audio=False)
        return output_path

video_creator = ReelsVideoCreator()
