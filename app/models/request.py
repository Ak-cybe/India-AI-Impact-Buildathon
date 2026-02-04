"""Request and response models for the Agentic Honeypot API"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime


class MessageContent(BaseModel):
    """Message content structure"""
    text: str = Field(..., description="Text content of the message")
    images: Optional[List[str]] = Field(default=None, description="List of image URLs or base64")
    audio: Optional[str] = Field(default=None, description="Audio URL or base64")
    links: Optional[List[str]] = Field(default=None, description="Extracted URLs")


class MessageMetadata(BaseModel):
    """Metadata about the message"""
    channel: str = Field(default="sms", description="Communication channel: sms, whatsapp, email")
    language: str = Field(default="en", description="Language code: en, hi, etc.")
    timestamp: Optional[datetime] = Field(default=None, description="Message timestamp")
    sender_id: Optional[str] = Field(default=None, description="Sender identifier")
    response_time: Optional[float] = Field(default=None, description="Response time in seconds")


class MessageRequest(BaseModel):
    """Incoming message request"""
    message: MessageContent = Field(..., description="Message content")
    sessionId: str = Field(..., description="Unique session identifier")
    metadata: Optional[MessageMetadata] = Field(default=None, description="Message metadata")
    conversationHistory: Optional[List[Dict[str, Any]]] = Field(default=None, description="Previous conversation turns")


class DetectionResult(BaseModel):
    """Scam detection result"""
    scam_detected: bool = Field(..., description="Whether scam was detected")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence score")
    scam_type: Optional[str] = Field(default=None, description="Type of scam detected")
    indicators: List[str] = Field(default=[], description="List of scam indicators found")
    contributing_agents: List[str] = Field(default=[], description="Agents that contributed to decision")


class IntelligenceItem(BaseModel):
    """Extracted intelligence item"""
    type: str = Field(..., description="Type: upi_id, bank_account, phone, link, email, etc.")
    value: str = Field(..., description="Extracted value")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence")
    timestamp: datetime = Field(default_factory=datetime.now, description="When extracted")


class MessageResponse(BaseModel):
    """Response to message request"""
    status: str = Field(..., description="Response status: success, error")
    reply: Optional[str] = Field(default=None, description="Agent's reply if scam detected")
    scam_detected: bool = Field(default=False, description="Whether scam was detected")
    session_active: bool = Field(default=False, description="Whether session should continue")
    intelligence_count: int = Field(default=0, description="Number of intelligence items extracted so far")


class FinalIntelligenceReport(BaseModel):
    """Final intelligence report for callback"""
    sessionId: str = Field(..., description="Session identifier")
    scamType: str = Field(..., description="Classified scam type")
    intelligenceGathered: List[Dict[str, Any]] = Field(..., description="All extracted intelligence")
    conversationTranscript: List[Dict[str, str]] = Field(..., description="Full conversation history")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence in findings")
    totalTurns: int = Field(..., description="Total conversation turns")
    timestamp: datetime = Field(default_factory=datetime.now, description="Report generation time")


class ImageAnalysisRequest(BaseModel):
    """Request for image-based scam analysis (Week 4)"""
    image_base64: str = Field(..., description="Base64 encoded image (with or without data URL prefix)")
    sessionId: Optional[str] = Field(default=None, description="Session ID to associate with")
    backend: Optional[str] = Field(default="auto", description="OCR backend: 'tesseract', 'gemini', or 'auto'")
    metadata: Optional[MessageMetadata] = Field(default=None, description="Message metadata")


class AdversarialCheckRequest(BaseModel):
    """Request for adversarial/AI detection check (Week 4)"""
    messages: List[str] = Field(..., description="List of scammer messages to analyze")
    timings: Optional[List[int]] = Field(default=None, description="Response times in milliseconds")
    sessionId: Optional[str] = Field(default=None, description="Session ID if applicable")

