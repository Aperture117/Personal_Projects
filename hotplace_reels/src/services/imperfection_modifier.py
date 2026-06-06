from PIL import Image, ImageEnhance, ImageFilter
import random
import os

class HumanTouch:
    @staticmethod
    def add_noise(img):
        """Adds subtle digital noise/grain to reduce perfection."""
        # Simplified: add some random pixel variations
        return img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))

    @staticmethod
    def shift_colors(img):
        """Simulates natural/indoor lighting by slightly shifting tints."""
        enhancer = ImageEnhance.Color(img)
        # Slightly desaturate or warm up
        return enhancer.enhance(random.uniform(0.9, 1.1))

    @staticmethod
    def micro_blur(img):
        """Simulates micro hand-shake or lens imperfections."""
        return img.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.2, 0.4)))

class Humanizer:
    """Transforms AI text into human-like messy text."""
    def transform(self, text: str) -> str:
        # 1. Remove formal endings
        text = text.replace("합니다", "함").replace("하세요", "하세여").replace("있습니다", "있음")
        # 2. Add informal '...' variants
        if random.random() > 0.5:
            text = text.replace("!", "!!").replace("?", "..?")
        # 3. Inject random emoji in middle
        words = text.split()
        if len(words) > 3:
            words.insert(len(words)//2, random.choice(["🔥", "✨", "👀", "🙌"]))
        return " ".join(words)

human_touch = HumanTouch()
humanizer = Humanizer()
