import json
import os
import time
import logging

logger = logging.getLogger(__name__)

class MLOpsService:
    def __init__(self, feedback_file: str = "data_storage/mlops_feedback.json"):
        self.feedback_file = feedback_file
        os.makedirs(os.path.dirname(self.feedback_file), exist_ok=True)
        if not os.path.exists(self.feedback_file):
            with open(self.feedback_file, "w") as f:
                json.dump([], f)

    def log_feedback(self, post_id: str, action: str, metadata: dict):
        """
        MLOps Feedback Loop: Records user approval/rejection.
        This data is used for Prompt Tuning and Model Evaluation.
        """
        try:
            with open(self.feedback_file, "r") as f:
                data = json.load(f)
            
            entry = {
                "timestamp": time.time(),
                "post_id": post_id,
                "action": action, # 'approved' or 'rejected'
                "metadata": metadata
            }
            data.append(entry)
            
            with open(self.feedback_file, "w") as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"📊 MLOps: Feedback recorded [{action}] for {post_id}")
        except Exception as e:
            logger.error(f"Failed to log MLOps feedback: {e}")

mlops_service = MLOpsService()
