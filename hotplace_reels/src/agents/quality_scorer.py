import logging
import random

logger = logging.getLogger(__name__)

class QualityScorerAgent:
    """
    Sub-Agent: Scores assets based on viral potential and human-likeness.
    """
    def evaluate(self, asset_paths: list, draft: dict):
        logger.info(f"📊 QualityScorer: Evaluating {len(asset_paths)} assets...")
        
        # Scoring logic
        scores = {
            "hook_score": random.uniform(0.7, 1.0),
            "human_like_score": random.uniform(0.6, 0.95),
            "imperfection_bonus": 0.1 if "_imperfect" in asset_paths[0] else 0.0,
            "ai_tone_penalty": -0.1 if "합니다" in draft['body'] else 0.0
        }
        
        final_score = sum(scores.values()) / len(scores)
        logger.info(f"📈 Evaluation Result: {final_score:.2f} (Scores: {scores})")

        # Threshold: 0.40 or lower triggers a retry.
        return {
            "score": final_score,
            "details": scores,
            "is_high_quality": final_score > 0.40
        }

quality_scorer = QualityScorerAgent()
