import os
import logging
import json
from src.core.config import settings
from google import genai
from google.genai import types
from pathlib import Path

logger = logging.getLogger(__name__)

class RemoteDevService:
    def __init__(self):
        # Set workspace root to 'Personal_Projects'
        self.workspace_root = Path(__file__).resolve().parent.parent.parent.parent
        
        # Use the same Gemini API as this CLI
        self.client = None
        if os.getenv("GOOGLE_API_KEY"):
            self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        
        logger.info(f"🚀 RemoteDev: Gemini 1.5 Brain Initialized at {self.workspace_root}")

    def list_files(self, sub_path: str = "") -> list:
        target_dir = self.workspace_root / sub_path
        files = []
        try:
            for root, dirs, filenames in os.walk(target_dir):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d != '.venv' and d != '__pycache__']
                for f in filenames:
                    files.append(str(Path(root).relative_to(self.workspace_root) / f))
                if len(files) > 100: break 
            return files
        except Exception as e:
            return [f"Error: {e}"]

    async def handle_instruction(self, instruction: str):
        """
        Uses Gemini 1.5 (CLI Intelligence) to execute remote code edits.
        """
        if not self.client:
            return "❌ GOOGLE_API_KEY가 설정되지 않아 Gemini Brain을 사용할 수 없습니다."

        file_list = self.list_files()
        
        prompt = f"""
        당신은 이 워크스페이스를 관리하는 'Gemini CLI 원격 에이전트'입니다.
        현재 워크스페이스 위치: {self.workspace_root}
        
        [전체 파일 목록]
        {file_list}
        
        [사용자 요청]
        "{instruction}"
        
        [미션]
        1. 요청을 수행하기 위해 수정해야 할 '가장 적절한 파일'을 목록에서 찾으세요.
        2. 해당 파일의 기존 코드 조각(old_string)과 바뀔 코드 조각(new_string)을 생성하세요.
        3. 코드는 생략 없이 정확하고 완성도 높게 작성하세요.
        
        반드시 아래 JSON 형식으로만 답변하세요:
        {{
          "file_path": "파일명 (목록에 있는 상대경로)",
          "old_string": "수정 전 코드 (정확히 일치해야 함)",
          "new_string": "수정 후 코드",
          "thought": "수정 이유 및 전략"
        }}
        """
        
        try:
            response = self.client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            
            plan = json.loads(response.text)
            full_path = self.workspace_root / plan['file_path']
            
            if not full_path.exists():
                return f"❌ 파일을 찾을 수 없습니다: {plan['file_path']}"

            with open(full_path, "r", encoding='utf-8') as f:
                content = f.read()

            if plan['old_string'] in content:
                new_content = content.replace(plan['old_string'], plan['new_string'])
                with open(full_path, "w", encoding='utf-8') as f:
                    f.write(new_content)
                
                logger.info(f"🛠️ RemoteDev: Successfully edited {plan['file_path']}")
                return f"✅ <b>수정 완료!</b>\n\n<b>파일</b>: {plan['file_path']}\n<b>생각</b>: {plan['thought']}"
            else:
                # Provide a snippet of the file to help the user identify the issue
                logger.error(f"Surgical edit failed. 'old_string' mismatch in {plan['file_path']}")
                return f"❌ <b>수정 실패</b>: 파일 내에서 일치하는 코드를 찾지 못했습니다.\n\n<b>찾으려던 코드</b>:\n<code>{plan['old_string'][:100]}...</code>"

        except Exception as e:
            logger.error(f"Gemini RemoteDev Error: {e}")
            return f"💥 <b>에이전트 오류</b>: {e}"

remote_dev_service = RemoteDevService()
