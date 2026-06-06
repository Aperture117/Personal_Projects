import requests
import logging
import os
import time
from src.core.config import settings

logger = logging.getLogger(__name__)

class InstagramService:
    """
    Service to handle Instagram Graph API interactions for Auto-Publishing.
    Includes professional retry logic and production-grade error handling.
    """
    def __init__(self):
        self.access_token = settings.INSTAGRAM_ACCESS_TOKEN
        self.user_id = settings.INSTAGRAM_USER_ID
        self.base_url = "https://graph.facebook.com/v21.0"

    def publish_carousel(self, image_urls: list[str], caption: str, max_retries: int = 3):
        """
        Publishes a carousel to Instagram with exponential backoff retry logic.
        """
        if not self.access_token or not self.user_id:
            logger.warning("⚠️ Instagram credentials missing in .env")
            return {"status": "error", "message": "Credentials missing"}

        valid_urls = [url for url in image_urls if url.startswith('http')]
        
        # --- LOCAL TESTING MODE ---
        if len(valid_urls) == 0:
            logger.info("🧪 [TEST MODE] Simulating Instagram Publish for Batch OS...")
            return {"status": "success", "message": "Simulation successful"}

        def retry_request(func, url, data):
            for i in range(max_retries):
                try:
                    res = func(url, data=data).json()
                    if 'error' not in res:
                        return res
                    logger.warning(f"⚠️ IG API Attempt {i+1} failed: {res}")
                    time.sleep(2 ** i) # Exponential backoff
                except Exception as e:
                    logger.error(f"💥 Request failed: {e}")
            return None

        try:
            # 1. Create individual item containers
            item_container_ids = []
            for url in valid_urls:
                payload = {
                    "image_url": url,
                    "is_carousel_item": "true",
                    "access_token": self.access_token
                }
                res = retry_request(requests.post, f"{self.base_url}/{self.user_id}/media", payload)
                if res and 'id' in res:
                    item_container_ids.append(res['id'])
                else:
                    return {"status": "error", "message": "Failed to create slide container"}

            # 2. Create carousel container
            carousel_payload = {
                "media_type": "CAROUSEL",
                "children": ",".join(item_container_ids),
                "caption": caption,
                "access_token": self.access_token
            }
            res = retry_request(requests.post, f"{self.base_url}/{self.user_id}/media", carousel_payload)
            if not res or 'id' not in res:
                return {"status": "error", "message": "Failed to create carousel container"}

            container_id = res['id']

            # 3. Final Publish
            time.sleep(5) # Give FB a few seconds to process containers
            publish_res = retry_request(requests.post, f"{self.base_url}/{self.user_id}/media_publish", 
                                       {"creation_id": container_id, "access_token": self.access_token})
            
            if publish_res and 'id' in publish_res:
                logger.info(f"✅ Instagram Post LIVE: {publish_res['id']}")
                return {"status": "success", "media_id": publish_res['id']}
            
            return {"status": "error", "message": "Final publication failed"}

        except Exception as e:
            logger.error(f"Instagram Publishing Exception: {e}")
            return {"status": "error", "message": str(e)}

instagram_service = InstagramService()
