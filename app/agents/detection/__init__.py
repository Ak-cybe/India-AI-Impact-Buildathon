"""Detection agents package - Scam detection using multi-agent consensus"""

from app.agents.detection.text_analyst import TextContentAnalyst
from app.agents.detection.link_checker import LinkSecurityChecker
from app.agents.detection.consensus import ConsensusDecisionAgent

# Week 4: Optional OCR agent
try:
    from app.agents.detection.ocr_agent import OCRAgent, AdversarialDetector, initialize_ocr
except ImportError:
    OCRAgent = None
    AdversarialDetector = None
    initialize_ocr = None

__all__ = [
    "TextContentAnalyst",
    "LinkSecurityChecker", 
    "ConsensusDecisionAgent",
    "OCRAgent",
    "AdversarialDetector",
    "initialize_ocr"
]
