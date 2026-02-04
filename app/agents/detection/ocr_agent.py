"""OCR Agent - Extracts text from images for scam detection (Week 4 Optional)"""

import re
import base64
import logging
from typing import Dict, List, Optional, Tuple
from io import BytesIO

# Lazy imports for optional dependencies
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

logger = logging.getLogger(__name__)


class OCRAgent:
    """
    Optical Character Recognition agent for extracting text from scam images
    
    Supports:
    - Tesseract OCR (local, fast, no API cost)
    - Google Gemini Vision (cloud, more accurate)
    - Base64 encoded images
    - URL-based images
    
    Common scam image types:
    - Fake bank screenshots
    - QR codes with payment links
    - Fake government notices
    - WhatsApp forwarded images
    """
    
    def __init__(self, google_api_key: str = None):
        self.google_api_key = google_api_key
        
        # Check available backends
        self.backends = []
        
        if PIL_AVAILABLE and TESSERACT_AVAILABLE:
            self.backends.append("tesseract")
            logger.info("[OCRAgent] Tesseract backend available")
        
        if GEMINI_AVAILABLE and google_api_key:
            genai.configure(api_key=google_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')
            self.backends.append("gemini")
            logger.info("[OCRAgent] Gemini Vision backend available")
        
        if not self.backends:
            logger.warning("[OCRAgent] No OCR backends available! Install pytesseract or set GOOGLE_API_KEY")
    
    def is_available(self) -> bool:
        """Check if OCR is available"""
        return len(self.backends) > 0
    
    def extract_text_from_base64(
        self,
        base64_data: str,
        backend: str = "auto"
    ) -> Dict:
        """
        Extract text from base64-encoded image
        
        Args:
            base64_data: Base64 encoded image string (with or without data URL prefix)
            backend: "tesseract", "gemini", or "auto" (tries fastest first)
            
        Returns:
            Dict with extracted text and intelligence
        """
        if not self.is_available():
            return {
                "success": False,
                "error": "no_ocr_backend",
                "message": "Install pytesseract or configure Gemini API"
            }
        
        try:
            # Clean base64 data (remove data URL prefix if present)
            if "," in base64_data:
                base64_data = base64_data.split(",")[1]
            
            # Decode to bytes
            image_bytes = base64.b64decode(base64_data)
            
            return self._process_image_bytes(image_bytes, backend)
            
        except Exception as e:
            logger.error(f"[OCRAgent] Error decoding base64: {e}")
            return {
                "success": False,
                "error": "decode_error",
                "message": str(e)
            }
    
    def _process_image_bytes(self, image_bytes: bytes, backend: str) -> Dict:
        """Process image bytes through OCR"""
        
        # Select backend
        if backend == "auto":
            # Prefer Gemini for accuracy, fallback to Tesseract
            backend = "gemini" if "gemini" in self.backends else "tesseract"
        
        if backend not in self.backends:
            return {
                "success": False,
                "error": "backend_unavailable",
                "message": f"Backend '{backend}' not available. Available: {self.backends}"
            }
        
        # Process with selected backend
        if backend == "tesseract":
            return self._ocr_tesseract(image_bytes)
        elif backend == "gemini":
            return self._ocr_gemini(image_bytes)
    
    def _ocr_tesseract(self, image_bytes: bytes) -> Dict:
        """OCR using Tesseract (local)"""
        try:
            # Load image
            image = Image.open(BytesIO(image_bytes))
            
            # Preprocess for better OCR
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Extract text
            text = pytesseract.image_to_string(image, lang='eng+hin')
            
            # Also try Hindi if available
            try:
                text_hin = pytesseract.image_to_string(image, lang='hin')
                if len(text_hin) > len(text):
                    text = text_hin
            except:
                pass  # Hindi not available
            
            # Extract intelligence
            intelligence = self._extract_intelligence_from_text(text)
            
            return {
                "success": True,
                "backend": "tesseract",
                "raw_text": text.strip(),
                "text_length": len(text),
                "intelligence": intelligence,
                "is_scam_likely": self._check_scam_indicators(text)
            }
            
        except Exception as e:
            logger.error(f"[OCRAgent] Tesseract error: {e}")
            return {
                "success": False,
                "backend": "tesseract",
                "error": str(e)
            }
    
    def _ocr_gemini(self, image_bytes: bytes) -> Dict:
        """OCR using Gemini Vision (cloud)"""
        try:
            # Create image part for Gemini
            image_part = {
                "mime_type": "image/jpeg",
                "data": base64.b64encode(image_bytes).decode()
            }
            
            # Prompt for scam detection context
            prompt = """Analyze this image and extract all text visible. Focus on:
1. Any phone numbers, UPI IDs, bank account numbers
2. Any URLs or links
3. Any email addresses
4. Any organization names being claimed (banks, government, etc.)

Format your response as:
EXTRACTED_TEXT:
[All visible text]

INTELLIGENCE:
- Phone: [any phone numbers found]
- UPI: [any UPI IDs found]
- URL: [any URLs found]
- Email: [any emails found]
- Organization: [any orgs mentioned]

SCAM_INDICATORS:
[List any suspicious elements that suggest this might be a scam message]"""
            
            # Call Gemini
            response = self.gemini_model.generate_content([prompt, image_part])
            
            # Parse response
            response_text = response.text
            
            # Extract sections
            raw_text = self._extract_section(response_text, "EXTRACTED_TEXT:")
            intelligence = self._parse_gemini_intelligence(response_text)
            scam_indicators = self._extract_section(response_text, "SCAM_INDICATORS:")
            
            return {
                "success": True,
                "backend": "gemini",
                "raw_text": raw_text,
                "text_length": len(raw_text),
                "intelligence": intelligence,
                "scam_indicators": scam_indicators,
                "is_scam_likely": bool(scam_indicators.strip())
            }
            
        except Exception as e:
            logger.error(f"[OCRAgent] Gemini error: {e}")
            return {
                "success": False,
                "backend": "gemini",
                "error": str(e)
            }
    
    def _extract_section(self, text: str, header: str) -> str:
        """Extract section from Gemini response"""
        if header not in text:
            return ""
        
        start = text.find(header) + len(header)
        
        # Find next header or end
        next_headers = ["EXTRACTED_TEXT:", "INTELLIGENCE:", "SCAM_INDICATORS:"]
        end = len(text)
        
        for h in next_headers:
            if h != header and h in text[start:]:
                pos = text.find(h, start)
                if pos < end:
                    end = pos
        
        return text[start:end].strip()
    
    def _parse_gemini_intelligence(self, text: str) -> List[Dict]:
        """Parse intelligence section from Gemini response"""
        intelligence = []
        section = self._extract_section(text, "INTELLIGENCE:")
        
        patterns = {
            "phone_number": r"Phone:\s*(.+)",
            "upi_id": r"UPI:\s*(.+)",
            "url": r"URL:\s*(.+)",
            "email": r"Email:\s*(.+)",
            "claimed_organization": r"Organization:\s*(.+)"
        }
        
        for intel_type, pattern in patterns.items():
            match = re.search(pattern, section, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if value and value.lower() not in ["none", "n/a", "-", "not found"]:
                    intelligence.append({
                        "type": intel_type,
                        "value": value,
                        "confidence": 0.85,
                        "source": "ocr_gemini"
                    })
        
        return intelligence
    
    def _extract_intelligence_from_text(self, text: str) -> List[Dict]:
        """Extract intelligence from OCR text using regex"""
        intelligence = []
        
        # Phone numbers
        phones = re.findall(r'(?:\+91[-\s]?)?[6-9]\d{9}', text)
        for phone in phones:
            intelligence.append({
                "type": "phone_number",
                "value": re.sub(r'[-\s]', '', phone),
                "confidence": 0.85,
                "source": "ocr_tesseract"
            })
        
        # UPI IDs
        upis = re.findall(r'[\w\.-]+@(?:ybl|paytm|okaxis|okicici|okhdfcbank|upi|sbi|hdfc)', text, re.IGNORECASE)
        for upi in upis:
            intelligence.append({
                "type": "upi_id",
                "value": upi.lower(),
                "confidence": 0.90,
                "source": "ocr_tesseract"
            })
        
        # URLs
        urls = re.findall(r'https?://[^\s\)<>]+', text)
        for url in urls:
            intelligence.append({
                "type": "url",
                "value": url,
                "confidence": 0.85,
                "source": "ocr_tesseract"
            })
        
        # Bank accounts (9-18 digits)
        accounts = re.findall(r'\b\d{9,18}\b', text)
        for acc in accounts:
            # Filter out phone numbers
            if not re.match(r'[6-9]\d{9}$', acc):
                intelligence.append({
                    "type": "bank_account",
                    "value": acc,
                    "confidence": 0.70,
                    "source": "ocr_tesseract"
                })
        
        return intelligence
    
    def _check_scam_indicators(self, text: str) -> bool:
        """Check for common scam indicators in text"""
        scam_phrases = [
            "urgent", "immediate action", "account blocked", "kyc",
            "verify now", "click here", "link expire", "limited time",
            "prize", "lottery", "winner", "claim now",
            "otp", "pin", "cvv", "password",
            "confirm your", "update your", "verify your"
        ]
        
        text_lower = text.lower()
        indicators_found = sum(1 for phrase in scam_phrases if phrase in text_lower)
        
        return indicators_found >= 2


class AdversarialDetector:
    """
    Detects if the scammer is using AI/automated responses
    
    Detection methods:
    - Response pattern analysis
    - Timing analysis
    - Vocabulary analysis
    - Consistency checking
    """
    
    def __init__(self):
        # AI-typical patterns
        self.ai_patterns = [
            r"as an ai",
            r"i don't have personal",
            r"i cannot provide",
            r"as a language model",
            r"i'm happy to help",
            r"certainly!",
            r"absolutely!",
            r"here's what",
            r"let me explain",
        ]
        
        # Human-like noise patterns
        self.human_noise = [
            r"umm+",
            r"hmm+",
            r"\.{3,}",  # Ellipsis
            r"!{2,}",   # Multiple exclamations
            r"\?\?+",   # Multiple question marks
        ]
    
    def analyze_message(self, message: str, timing_ms: int = None) -> Dict:
        """
        Analyze if message is AI-generated
        
        Args:
            message: The scammer's message
            timing_ms: Response time in milliseconds
            
        Returns:
            Analysis result with AI probability
        """
        scores = []
        reasons = []
        
        # Check AI patterns
        ai_pattern_count = 0
        for pattern in self.ai_patterns:
            if re.search(pattern, message.lower()):
                ai_pattern_count += 1
        
        if ai_pattern_count > 0:
            scores.append(min(ai_pattern_count * 0.2, 0.5))
            reasons.append(f"AI-typical phrases detected ({ai_pattern_count})")
        
        # Check human noise
        human_noise_count = 0
        for pattern in self.human_noise:
            if re.search(pattern, message):
                human_noise_count += 1
        
        if human_noise_count == 0 and len(message) > 100:
            scores.append(0.2)
            reasons.append("No human noise in long message")
        
        # Timing analysis
        if timing_ms is not None:
            if timing_ms < 1000:  # < 1 second
                scores.append(0.4)
                reasons.append(f"Very fast response ({timing_ms}ms)")
            elif timing_ms < 3000:  # < 3 seconds
                scores.append(0.2)
                reasons.append(f"Fast response ({timing_ms}ms)")
        
        # Vocabulary analysis
        words = message.split()
        if len(words) > 20:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio > 0.9:  # High vocabulary diversity
                scores.append(0.15)
                reasons.append(f"High vocabulary diversity ({unique_ratio:.2f})")
        
        # Calculate final probability
        ai_probability = min(sum(scores), 0.95) if scores else 0.1
        
        return {
            "is_likely_ai": ai_probability > 0.5,
            "ai_probability": round(ai_probability, 2),
            "confidence": 0.6 if scores else 0.3,
            "reasons": reasons,
            "recommendation": "continue_engagement" if ai_probability < 0.7 else "flag_for_review"
        }
    
    def analyze_conversation(self, messages: List[str], timings: List[int] = None) -> Dict:
        """
        Analyze full conversation for AI patterns
        
        Args:
            messages: List of scammer messages
            timings: List of response times in ms
            
        Returns:
            Conversation-level analysis
        """
        if not messages:
            return {"error": "no_messages"}
        
        # Analyze each message
        analyses = []
        for i, msg in enumerate(messages):
            timing = timings[i] if timings and i < len(timings) else None
            analyses.append(self.analyze_message(msg, timing))
        
        # Aggregate
        avg_probability = sum(a["ai_probability"] for a in analyses) / len(analyses)
        
        # Consistency check: AI tends to be more consistent
        probabilities = [a["ai_probability"] for a in analyses]
        variance = sum((p - avg_probability) ** 2 for p in probabilities) / len(probabilities)
        
        if variance < 0.02 and len(analyses) > 3:  # Very consistent
            avg_probability = min(avg_probability + 0.1, 0.95)
        
        return {
            "is_likely_ai": avg_probability > 0.5,
            "ai_probability": round(avg_probability, 2),
            "message_count": len(messages),
            "consistency_score": round(1 - variance, 2),
            "individual_analyses": analyses,
            "recommendation": "terminate" if avg_probability > 0.8 else "continue"
        }


# Global instances
ocr_agent: Optional[OCRAgent] = None
adversarial_detector = AdversarialDetector()


def initialize_ocr(google_api_key: str = None):
    """Initialize OCR agent with API key"""
    global ocr_agent
    ocr_agent = OCRAgent(google_api_key)
    return ocr_agent
