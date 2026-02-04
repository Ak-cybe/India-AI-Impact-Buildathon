"""Link Security Checker Agent - URL analysis and phishing detection"""

import re
import httpx
from typing import Dict, List
from urllib.parse import urlparse
from app.config import settings


class LinkSecurityChecker:
    """
    Checks URLs for malicious content using Google Safe Browsing API
    and heuristic analysis (shortened URLs, suspicious domains)
    Based on MINERVA framework link checking component
    """
    
    def __init__(self):
        self.api_key = settings.safe_browsing_api_key
        self.shortened_domains = [
            "bit.ly", "tinyurl.com", "goo.gl", "ow.ly", "t.co", 
            "buff.ly", "adf.ly", "is.gd", "cli.gs", "tiny.cc"
        ]
        
        # Suspicious TLDs often used in scams
        self.suspicious_tlds = [
            ".tk", ".ml", ".ga", ".cf", ".gq",  # Free domains
            ".xyz", ".top", ".work", ".click"
        ]
        
        # URL extraction pattern
        self.url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
    
    async def analyze(self, text: str) -> Dict:
        """
        Analyze URLs in text for security threats
        
        Args:
            text: Message text containing URLs
            
        Returns:
            Dict with threat analysis results
        """
        # Extract URLs
        urls = self.url_pattern.findall(text)
        
        if not urls:
            return {
                "agent": "link_checker",
                "risk_score": 0.0,
                "confidence": 1.0,
                "threats_found": 0,
                "threat_details": [],
                "urls_analyzed": 0
            }
        
        threats = []
        
        for url in urls:
            # Heuristic checks (fast)
            domain = urlparse(url).netloc
            
            # Check for URL shorteners (red flag)
            if any(short in domain for short in self.shortened_domains):
                threats.append({
                    "url": url,
                    "type": "shortened_url",
                    "risk": "high",
                    "reason": "URL shortener detected - often used to hide phishing links"
                })
            
            # Check for suspicious TLDs
            if any(domain.endswith(tld) for tld in self.suspicious_tlds):
                threats.append({
                    "url": url,
                    "type": "suspicious_domain",
                    "risk": "medium",
                    "reason": f"Suspicious TLD - domain uses {domain}"
                })
            
            # Check for IP address instead of domain (suspicious)
            if re.match(r'^\d+\.\d+\.\d+\.\d+$', domain):
                threats.append({
                    "url": url,
                    "type": "ip_address_url",
                    "risk": "high",
                    "reason": "URL uses IP address instead of domain name"
                })
            
            # Google Safe Browsing check (if API key available)
            if self.api_key:
                is_phishing = await self.check_safe_browsing(url)
                if is_phishing:
                    threats.append({
                        "url": url,
                        "type": "phishing",
                        "risk": "critical",
                        "reason": "Google Safe Browsing flagged as malicious"
                    })
        
        # Calculate risk score
        risk_score = min(len(threats) * 0.4, 1.0)
        
        # Higher risk if multiple threats or critical threats found
        critical_count = sum(1 for t in threats if t["risk"] == "critical")
        if critical_count > 0:
            risk_score = min(risk_score + 0.3, 1.0)
        
        return {
            "agent": "link_checker",
            "risk_score": round(risk_score, 3),
            "confidence": 0.95,  # High confidence in link analysis
            "threats_found": len(threats),
            "threat_details": threats,
            "urls_analyzed": len(urls),
            "indicators": ["malicious_link"] if len(threats) > 0 else []
        }
    
    async def check_safe_browsing(self, url: str) -> bool:
        """
        Check URL against Google Safe Browsing API
        
        Args:
            url: URL to check
            
        Returns:
            True if URL is flagged as malicious, False otherwise
        """
        if not self.api_key:
            # Skip if no API key configured
            return False
        
        endpoint = "https://safebrowsing.googleapis.com/v4/threatMatches:find"
        
        payload = {
            "client": {
                "clientId": "honeypot-scam-detector",
                "clientVersion": "1.0.0"
            },
            "threatInfo": {
                "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE"],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [{"url": url}]
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{endpoint}?key={self.api_key}",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return len(result.get("matches", [])) > 0
                else:
                    # API error - assume safe (fail open for availability)
                    return False
                    
        except Exception as e:
            # Network error - fail open
            print(f"Safe Browsing API error: {e}")
            return False
    
    def extract_urls(self, text: str) -> List[str]:
        """Extract all URLs from text"""
        return self.url_pattern.findall(text)
