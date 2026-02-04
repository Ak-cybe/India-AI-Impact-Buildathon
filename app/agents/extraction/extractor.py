"""Intelligence Extractor - Real-time extraction and validation of scammer information"""

import re
from typing import Dict, List, Optional
from datetime import datetime


class IntelligenceExtractor:
    """
    Extracts structured intelligence from scammer messages
    
    Types of intelligence:
    - UPI IDs
    - Phone numbers
    - Bank accounts
    - URLs
    - Emails
    - App names / download links
    - Crypto wallet addresses
    - Organization claims
    """
    
    def __init__(self):
        # Compile regex patterns for efficiency
        self.patterns = {
            "upi_id": re.compile(r'\b[\w\.-]+@(?:ybl|paytm|okaxis|okicici|okhdfcbank|upi|ibl|freecharge|apl|waicici|waaxis|wahdfcbank|axisbank|sbi|icici|hdfc|kotak|indus)\b', re.IGNORECASE),
            "phone_india": re.compile(r'(?:\+91[-\s]?)?[6-9]\d{9}'),
            "phone_intl": re.compile(r'\+\d{1,3}[-\s]?\d{6,12}'),
            "bank_account": re.compile(r'\b\d{9,18}\b'),
            "ifsc_code": re.compile(r'\b[A-Z]{4}0[A-Z0-9]{6}\b'),
            "url": re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+'),
            "shortened_url": re.compile(r'(?:bit\.ly|tinyurl\.com|goo\.gl|ow\.ly|t\.co|buff\.ly)/[\w-]+'),
            "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            "crypto_btc": re.compile(r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b'),
            "crypto_eth": re.compile(r'\b0x[a-fA-F0-9]{40}\b'),
            "pan_card": re.compile(r'\b[A-Z]{5}\d{4}[A-Z]\b'),
            "aadhar": re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'),
        }
        
        # Known scam app names
        self.known_scam_apps = [
            "anydesk", "teamviewer", "quicksupport", "aeroadmin",
            "screenshare", "remote desktop", "ammyy admin"
        ]
        
        # Known bank impersonation keywords
        self.bank_keywords = [
            "sbi", "hdfc", "icici", "axis", "kotak", "pnb", "bob",
            "canara", "union", "rbi", "reserve bank"
        ]
    
    def extract_all(self, text: str, metadata: Dict = None) -> List[Dict]:
        """
        Extract all intelligence items from text
        
        Args:
            text: Message text to analyze
            metadata: Optional metadata (sender info, timestamp, etc.)
            
        Returns:
            List of intelligence items with type, value, confidence
        """
        intelligence = []
        timestamp = datetime.now().isoformat()
        
        # Extract UPI IDs
        upi_matches = self.patterns["upi_id"].findall(text)
        for upi in set(upi_matches):
            intelligence.append({
                "type": "upi_id",
                "value": upi.lower(),
                "confidence": 0.95,
                "timestamp": timestamp,
                "source": "message_content"
            })
        
        # Extract phone numbers
        phone_matches = self.patterns["phone_india"].findall(text)
        for phone in set(phone_matches):
            cleaned = re.sub(r'[-\s]', '', phone)
            intelligence.append({
                "type": "phone_number",
                "value": cleaned,
                "confidence": 0.90,
                "timestamp": timestamp,
                "source": "message_content"
            })
        
        # Extract international phone numbers
        intl_phones = self.patterns["phone_intl"].findall(text)
        for phone in set(intl_phones):
            cleaned = re.sub(r'[-\s]', '', phone)
            if cleaned not in [i["value"] for i in intelligence if i["type"] == "phone_number"]:
                intelligence.append({
                    "type": "phone_number",
                    "value": cleaned,
                    "confidence": 0.85,
                    "timestamp": timestamp,
                    "source": "message_content",
                    "note": "international"
                })
        
        # Extract URLs
        urls = self.patterns["url"].findall(text)
        for url in set(urls):
            is_shortened = bool(self.patterns["shortened_url"].search(url))
            intelligence.append({
                "type": "url",
                "value": url,
                "confidence": 0.95,
                "timestamp": timestamp,
                "source": "message_content",
                "is_shortened": is_shortened,
                "risk": "high" if is_shortened else "medium"
            })
        
        # Extract shortened URLs (standalone mentions like "bit.ly/xyz")
        shortened = self.patterns["shortened_url"].findall(text)
        existing_urls = [i["value"] for i in intelligence if i["type"] == "url"]
        for short in set(shortened):
            full_url = f"https://{short}"
            if full_url not in existing_urls and short not in existing_urls:
                intelligence.append({
                    "type": "url",
                    "value": full_url,
                    "confidence": 0.90,
                    "timestamp": timestamp,
                    "source": "message_content",
                    "is_shortened": True,
                    "risk": "high"
                })
        
        # Extract emails (excluding UPI IDs)
        emails = self.patterns["email"].findall(text)
        upi_values = [i["value"] for i in intelligence if i["type"] == "upi_id"]
        for email in set(emails):
            if email.lower() not in upi_values:
                intelligence.append({
                    "type": "email",
                    "value": email.lower(),
                    "confidence": 0.90,
                    "timestamp": timestamp,
                    "source": "message_content"
                })
        
        # Extract bank accounts (with context validation)
        accounts = self.patterns["bank_account"].findall(text)
        for acc in set(accounts):
            # Basic validation: not a phone number
            if len(acc) >= 9 and not self.patterns["phone_india"].match(acc):
                intelligence.append({
                    "type": "bank_account",
                    "value": acc,
                    "confidence": 0.70,  # Lower confidence without context
                    "timestamp": timestamp,
                    "source": "message_content"
                })
        
        # Extract IFSC codes
        ifsc_codes = self.patterns["ifsc_code"].findall(text)
        for ifsc in set(ifsc_codes):
            intelligence.append({
                "type": "ifsc_code",
                "value": ifsc.upper(),
                "confidence": 0.95,
                "timestamp": timestamp,
                "source": "message_content"
            })
        
        # Extract crypto wallets
        btc_wallets = self.patterns["crypto_btc"].findall(text)
        for wallet in set(btc_wallets):
            intelligence.append({
                "type": "crypto_wallet_btc",
                "value": wallet,
                "confidence": 0.85,
                "timestamp": timestamp,
                "source": "message_content"
            })
        
        eth_wallets = self.patterns["crypto_eth"].findall(text)
        for wallet in set(eth_wallets):
            intelligence.append({
                "type": "crypto_wallet_eth",
                "value": wallet,
                "confidence": 0.90,
                "timestamp": timestamp,
                "source": "message_content"
            })
        
        # Extract scam app mentions
        text_lower = text.lower()
        for app in self.known_scam_apps:
            if app in text_lower:
                intelligence.append({
                    "type": "scam_app_mention",
                    "value": app,
                    "confidence": 0.80,
                    "timestamp": timestamp,
                    "source": "message_content",
                    "risk": "high"
                })
        
        # Extract bank impersonation claims
        for bank in self.bank_keywords:
            if bank in text_lower:
                intelligence.append({
                    "type": "claimed_organization",
                    "value": bank.upper(),
                    "confidence": 0.75,
                    "timestamp": timestamp,
                    "source": "message_content"
                })
                break  # Only record first match
        
        return intelligence
    
    def validate_upi_id(self, upi_id: str) -> bool:
        """Validate UPI ID format"""
        return bool(self.patterns["upi_id"].match(upi_id))
    
    def validate_phone(self, phone: str) -> bool:
        """Validate Indian phone number"""
        cleaned = re.sub(r'[-\s+]', '', phone)
        return len(cleaned) == 10 or len(cleaned) == 12
    
    def deduplicate_intelligence(self, items: List[Dict]) -> List[Dict]:
        """Remove duplicate intelligence items"""
        seen = set()
        unique = []
        
        for item in items:
            key = (item["type"], item["value"])
            if key not in seen:
                seen.add(key)
                unique.append(item)
        
        return unique
    
    def filter_high_confidence(self, items: List[Dict], threshold: float = 0.75) -> List[Dict]:
        """Filter items by confidence threshold"""
        return [item for item in items if item.get("confidence", 0) >= threshold]
    
    def get_summary(self, items: List[Dict]) -> Dict:
        """Get summary statistics of intelligence items"""
        by_type = {}
        for item in items:
            item_type = item["type"]
            by_type[item_type] = by_type.get(item_type, 0) + 1
        
        high_risk = [i for i in items if i.get("risk") == "high"]
        
        return {
            "total_items": len(items),
            "by_type": by_type,
            "high_risk_count": len(high_risk),
            "avg_confidence": sum(i.get("confidence", 0) for i in items) / len(items) if items else 0
        }
