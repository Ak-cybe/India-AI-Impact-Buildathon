"""Text Content Analyst Agent - Linguistic pattern detection"""

from typing import Dict, List
import re


class TextContentAnalyst:
    """
    Analyzes text messages for linguistic patterns and psychological triggers
    Based on research from MINERVA framework and scam pattern analysis
    """
    
    def __init__(self):
        # Keyword categories from research
        self.urgency_keywords = [
            "urgent", "immediate", "now", "today", "tonight", "blocked", 
            "suspended", "expires", "deadline", "limited time", "act now"
        ]
        
        self.financial_keywords = [
            "otp", "cvv", "pin", "upi", "account", "bank", "payment", 
            "transfer", "money", "rupees", "verify", "kyc", "pan card",
            "aadhar", "credit card", "debit card", "wallet"
        ]
        
        self.authority_keywords = [
            "bank", "government", "police", "rbi", "income tax", "it department",
            "law enforcement", "legal action", "court", "sebi", "customs",
            "ministry", "official", "authorized", "certified"
        ]
        
        self.threat_keywords = [
            "arrest", "fine", "penalty", "jail", "legal action", "lawsuit",
            "criminal case", "investigation", "warrant", "confiscate", "seize"
        ]
        
        # Psychological trigger phrases
        self.urgency_phrases = [
            "within 24 hours", "before tonight", "expires today", "last chance",
            "final notice", "immediate action required", "act before"
        ]
        
        # UPI ID pattern
        self.upi_pattern = re.compile(r'\b[\w\.-]+@[\w\.-]+\b')
        
        # Phone number patterns (Indian)
        self.phone_pattern = re.compile(r'(\+91[\s-]?)?[6-9]\d{9}')
        
        # Bank account pattern (basic)
        self.bank_account_pattern = re.compile(r'\b\d{9,18}\b')
    
    async def analyze(self, text: str) -> Dict:
        """
        Analyze text for scam indicators
        
        Args:
            text: Message text to analyze
            
        Returns:
            Dict with analysis results including risk_score, indicators, etc.
        """
        text_lower = text.lower()
        
        # Count keyword matches
        urgency_score = sum(1 for kw in self.urgency_keywords if kw in text_lower) / len(self.urgency_keywords)
        financial_score = sum(1 for kw in self.financial_keywords if kw in text_lower) / len(self.financial_keywords)
        authority_score = sum(1 for kw in self.authority_keywords if kw in text_lower) / len(self.authority_keywords)
        threat_score = sum(1 for kw in self.threat_keywords if kw in text_lower) / len(self.threat_keywords)
        
        # Check for psychological triggers
        has_urgency_phrase = any(phrase in text_lower for phrase in self.urgency_phrases)
        has_time_pressure = has_urgency_phrase or urgency_score > 0.15
        
        # Detect financial identifiers
        has_upi = bool(self.upi_pattern.search(text))
        has_phone = bool(self.phone_pattern.search(text))
        has_account = bool(self.bank_account_pattern.search(text))
        
        # Check for common scam patterns
        requesting_credentials = any(word in text_lower for word in ["send otp", "share otp", "give pin", "enter cvv"])
        claiming_authority = authority_score > 0.1 and (threat_score > 0.05 or urgency_score > 0.1)
        
        # Calculate indicators
        indicators = []
        if has_time_pressure:
            indicators.append("urgency_tactic")
        if requesting_credentials:
            indicators.append("credential_request")
        if claiming_authority:
            indicators.append("authority_impersonation")
        if threat_score > 0.1:
            indicators.append("threatening_language")
        if has_upi or has_phone or has_account:
            indicators.append("financial_identifiers_present")
        
        # Calculate composite risk score
        risk_score = (
            urgency_score * 0.25 +
            financial_score * 0.30 +
            authority_score * 0.20 +
            threat_score * 0.25
        )
        
        # Boost if multiple indicators present
        if len(indicators) >= 2:
            risk_score = min(risk_score * 1.3, 1.0)
        
        # Psychological tactics detected
        psychological_tactics = []
        if has_time_pressure:
            psychological_tactics.append("urgency")
        if threat_score > 0.1:
            psychological_tactics.append("fear")
        if claiming_authority:
            psychological_tactics.append("authority")
        
        return {
            "agent": "text_analyst",
            "risk_score": round(risk_score, 3),
            "confidence": 0.8,  # High confidence in keyword matching
            "indicators": indicators,
            "psychological_tactics": psychological_tactics,
            "scores": {
                "urgency": round(urgency_score, 3),
                "financial": round(financial_score, 3),
                "authority": round(authority_score, 3),
                "threat": round(threat_score, 3)
            },
            "financial_entities_detected": {
                "upi_id": has_upi,
                "phone_number": has_phone,
                "account_number": has_account
            }
        }
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract financial entities from text"""
        return {
            "upi_ids": self.upi_pattern.findall(text),
            "phone_numbers": self.phone_pattern.findall(text),
            "account_numbers": self.bank_account_pattern.findall(text)
        }
