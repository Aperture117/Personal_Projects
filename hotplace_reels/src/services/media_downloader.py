import requests
import os
import logging
from src.core.config import settings

logger = logging.getLogger(__name__)

class MediaDownloader:
    def __init__(self, base_path: str = "data_storage/temp_media"):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    def download_images(self, place_name: str, urls: list[str]) -> list[str]:
        """
        Downloads a list of images and returns local file paths.
        """
        local_paths = []
        place_folder = os.path.join(self.base_path, place_name.replace(" ", "_"))
        os.makedirs(place_folder, exist_ok=True)

        for i, url in enumerate(urls):
            try:
                response = requests.get(url, timeout=10, stream=True)
                if response.status_code == 200:
                    ext = url.split(".")[-1].split("?")[0]
                    if len(ext) > 4: ext = "jpg" # Default to jpg
                    
                    path = os.path.join(place_folder, f"image_{i}.{ext}")
                    with open(path, 'wb') as f:
                        for chunk in response.iter_content(1024):
                            f.write(chunk)
                    local_paths.append(path)
            except Exception as e:
                logger.error(f"Download failed for {url}: {e}")
        
        return local_paths

media_downloader = MediaDownloader()
