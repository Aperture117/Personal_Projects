import ollama
from src.core.config import settings
import logging
from google import genai
from google.genai import types
import json
import os

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        # Fallback to gemma4:e2b if LLM_MODEL is not set properly
        self.model = settings.LLM_MODEL if settings.LLM_MODEL else "gemma4:e2b"
        self.client = ollama.Client(host=settings.OLLAMA_HOST)
        
        # Cloud Vision LLM via Google Gemini
        self.genai_client = None
        if os.getenv("GOOGLE_API_KEY"):
            self.genai_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

    def analyze_visual_structure(self, image_path: str) -> dict:
        """
        Analyze an image using local Ollama (llama3.2-vision) to extract its visual layout.
        Completely FREE and private.
        """
        # 1. Validation: Check if file exists
        if not image_path or not os.path.exists(image_path):
            logger.warning(f"⚠️ Image not found at {image_path}. Returning mock layout for testing.")
            return self._get_mock_layout()

        try:
            # 2. Vision Analysis
            response = self.client.generate(
                model="llama3.2-vision",
                prompt="""
                Analyze this Instagram slide and extract its visual structure as JSON.
                JSON structure:
                {
                  "background": "description of background scene",
                  "layout_nodes": [{"type": "text", "position": "top/center/bottom", "size": "large/small", "content": "text content"}],
                  "color_palette": ["#hex_bg", "#hex_text"],
                  "font_style": "Bold Sans-serif / Serif / Handwritten",
                  "text_content": "full text"
                }
                Return ONLY the raw JSON.
                """,
                images=[image_path],
                format="json"
            )
            
            return json.loads(response['response'])
        except Exception as e:
            logger.error(f"Local Vision Analysis Error (Ollama): {e}")
            return self._get_mock_layout()

    def _get_mock_layout(self):
        return {
            "background": "Minimalist aesthetic cafe interior",
            "layout_nodes": [{"type": "text", "position": "center", "size": "large"}],
            "color_palette": ["#FFFFFF", "#000000"],
            "font_style": "Bold Sans-serif"
        }

    def plan_visual_replication(self, viral_layout: dict, new_topic: str) -> dict:
        """
        Create a prompt for image generation that mimics the viral layout but with new content.
        """
        prompt = f"""
        당신은 최고의 인스타그램 비주얼 디자이너입니다.
        아래의 [레퍼런스 레이아웃]을 100% 복제하여 [새로운 주제]에 맞는 이미지를 기획해주세요.
        
        [레퍼런스 레이아웃]
        - 배경: {viral_layout.get('background')}
        - 폰트 스타일: {viral_layout.get('font_style')}
        - 색감: {viral_layout.get('color_palette')}
        - 구성 요소: {viral_layout.get('layout_nodes')}
        
        [새로운 주제]
        - {new_topic}
        
        [결과물 형식]
        1. Image Generation Prompt: 레퍼런스의 구도와 색감을 유지하면서 {new_topic}을 표현하는 영어 프롬프트.
        2. Overlay Text: 레퍼런스의 위치에 들어갈 새로운 텍스트 내용 (한국어).
        3. Visual Instructions: 제작 시 주의할 점 (폰트 크기, 여백 등).
        
        JSON으로 답변해주세요.
        """
        
        try:
            response = self.client.generate(model=self.model, prompt=prompt, format="json")
            return json.loads(response['response'])
        except Exception as e:
            logger.error(f"Planning Error: {e}")
            return {"error": "Planning failed"}

    def generate_content(self, prompt_type: str, place_name: str, context: str, style: str = "viral_list") -> str:
        # (Existing logic remains)
        # Define Viral Templates
        templates = {
            "viral_list": f"주제: {place_name}을 포함한 핫플 리스트. 스타일: '저장 안 하면 손해' 느낌의 정보 전달형.",
            "pov": f"주제: {place_name}. 스타일: 'POV(Point of View)' 시점의 1인칭 공감형. 친근한 반말 사용.",
            "secret_gem": f"주제: {place_name}. 스타일: '나만 알고 싶은 곳' 컨셉의 신비주의 및 반전형.",
            "urgent": f"주제: {place_name}. 스타일: '지금 당장 가야 함' 느낌의 속도감 있고 자극적인 멘트.",
            "instagram_feed": f"주제: {place_name} 피드 게시물. 스타일: 감성적이고 상세한 설명이 담긴 블로그형 피드."
        }
        
        selected_style = templates.get(style, templates["viral_list"])
        
        # Adjust prompt based on type (Reels vs Feed)
        if prompt_type == "feed":
            prompt = f"""
            당신은 인스타그램 팔로워 50만 명을 보유한 감성 인플루언서입니다.
            {place_name}에 대한 '인스타그램 피드 게시물'을 작성해주세요.
            
            [게시물 구성]
            1. 감성 캡션: 첫 줄에 시선을 끄는 감성적인 문구
            2. 상세 설명: 장소의 분위기, 메뉴, 팁 등을 다정하게 설명
            3. 카드뉴스 구성: 슬라이드 1~5번에 들어갈 핵심 텍스트 내용 요약
            4. 해시태그: {place_name}와 관련된 인기 해시태그 15개
            
            상황: {context}
            한국어로 작성하고 인스타그램 특유의 이모지를 적절히 사용해주세요.
            """
        else:
            prompt = f"""
            당신은 조회수 1,000만 회를 기록하는 최고의 릴스 기획자입니다.
            아래 정보를 바탕으로 {selected_style} 대본을 작성해주세요.
            
            [정보]
            장소: {place_name}
            상황: {context}
            
            [대본 필수 구성 요소]
            1. 강력한 훅(Hook): 첫 3초 안에 무조건 멈추게 할 문구 (예: "여기 모르면 간첩 소리 들음")
            2. 본론: 핵심 장점 2-3개를 아주 짧고 힙하게 (문장당 5단어 이내)
            3. 저장 유도: 자연스럽게 '저장' 버튼을 누르게 하는 멘트
            4. 행동 유도: "성수 같이 갈 친구 태그" 등 댓글 유도
            
            한국어로 작성하고, 릴스 영상 편집을 위한 컷 전환 포인트도 표시해주세요.
            """
        
        try:
            response = self.client.generate(model=self.model, prompt=prompt)
            return response['response']
        except Exception as e:
            logger.error(f"AI Generation Error: {e}")
            return f"AI 생성 오류: {place_name}는 현재 매우 핫한 장소입니다!"

ai_service = AIService()
