"""Input Sanitizer - Protection against prompt injection and malicious input"""

import re
import html
from typing import Dict, List, Optional, Tuple


class InputSanitizer:
    """
    Sanitizes and validates user input to prevent:
    - Prompt injection attacks
    - XSS attacks
    - SQL injection patterns
    - Malicious payloads
    """
    
    # Prompt injection patterns
    PROMPT_INJECTION_PATTERNS = [
        r"ignore\s*(previous|above|all)\s*(instructions?|prompts?|rules?)",
        r"forget\s*(everything|all|your)\s*(instructions?|training)?",
        r"you\s*are\s*now\s*(a|an|the)",
        r"new\s*instructions?:",
        r"system\s*prompt:",
        r"\\n\\n(human|user|assistant):",
        r"<\|.*\|>",  # Special tokens
        r"\[\[.*\]\]",  # Bracket injection
        r"{{.*}}",  # Template injection
        r"pretend\s*(you\s*are|to\s*be)",
        r"act\s*as\s*(if|though)",
        r"roleplay\s*as",
        r"jailbreak",
        r"dan\s*mode",  # DAN jailbreak
        r"do\s*anything\s*now",
        r"bypass\s*(safety|filter|restrictions?)",
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",  # onclick, onerror, etc.
        r"<iframe",
        r"<object",
        r"<embed",
        r"<svg\s*onload",
        r"data:text/html",
    ]
    
    # SQL injection patterns
    SQL_PATTERNS = [
        r"(\b(union|select|insert|update|delete|drop|alter)\b.*\b(from|into|table|database)\b)",
        r"(--)|(;--)",
        r"(\bor\b.*=.*\bor\b)",
        r"(\'.*\bor\b.*\')",
    ]
    
    # Suspicious unicode/control characters
    SUSPICIOUS_CHARS = [
        '\u0000',  # Null
        '\u200b',  # Zero-width space
        '\u200c',  # Zero-width non-joiner
        '\u200d',  # Zero-width joiner
        '\u2028',  # Line separator
        '\u2029',  # Paragraph separator
        '\ufeff',  # BOM
    ]
    
    def __init__(self, max_length: int = 4096):
        """
        Initialize sanitizer
        
        Args:
            max_length: Maximum allowed input length
        """
        self.max_length = max_length
        
        # Compile patterns for efficiency
        self.prompt_injection_regex = [
            re.compile(p, re.IGNORECASE | re.DOTALL) 
            for p in self.PROMPT_INJECTION_PATTERNS
        ]
        self.xss_regex = [
            re.compile(p, re.IGNORECASE | re.DOTALL) 
            for p in self.XSS_PATTERNS
        ]
        self.sql_regex = [
            re.compile(p, re.IGNORECASE) 
            for p in self.SQL_PATTERNS
        ]
    
    def sanitize(self, text: str) -> Tuple[str, List[str]]:
        """
        Sanitize input text
        
        Args:
            text: Raw input text
            
        Returns:
            (sanitized_text, list_of_warnings)
        """
        warnings = []
        
        if not text:
            return "", []
        
        # Check length
        if len(text) > self.max_length:
            text = text[:self.max_length]
            warnings.append(f"Input truncated to {self.max_length} characters")
        
        # Remove suspicious unicode characters
        for char in self.SUSPICIOUS_CHARS:
            if char in text:
                text = text.replace(char, '')
                warnings.append(f"Removed suspicious character: {repr(char)}")
        
        # HTML escape (prevents XSS)
        text = html.escape(text)
        
        return text, warnings
    
    def validate(self, text: str) -> Tuple[bool, List[str]]:
        """
        Validate input for security threats
        
        Args:
            text: Input text to validate
            
        Returns:
            (is_safe, list_of_threats)
        """
        threats = []
        
        if not text:
            return True, []
        
        # Check for prompt injection
        for pattern in self.prompt_injection_regex:
            if pattern.search(text):
                threats.append(f"Prompt injection pattern detected: {pattern.pattern[:50]}...")
        
        # Check for XSS
        for pattern in self.xss_regex:
            if pattern.search(text):
                threats.append(f"XSS pattern detected: {pattern.pattern[:50]}...")
        
        # Check for SQL injection
        for pattern in self.sql_regex:
            if pattern.search(text):
                threats.append(f"SQL injection pattern detected")
        
        is_safe = len(threats) == 0
        return is_safe, threats
    
    def process(self, text: str) -> Dict:
        """
        Full processing: sanitize and validate
        
        Args:
            text: Raw input text
            
        Returns:
            Dict with sanitized text, safety status, and any warnings/threats
        """
        # Validate first (on raw input)
        is_safe, threats = self.validate(text)
        
        # Sanitize
        sanitized, warnings = self.sanitize(text)
        
        return {
            "original_length": len(text) if text else 0,
            "sanitized_text": sanitized,
            "sanitized_length": len(sanitized),
            "is_safe": is_safe,
            "threats": threats,
            "warnings": warnings,
            "blocked": len(threats) > 0
        }
    
    def sanitize_for_llm(self, text: str) -> str:
        """
        Special sanitization for text going to LLM
        
        Removes/escapes content that could affect LLM behavior
        """
        if not text:
            return ""
        
        # Process normally first
        result = self.process(text)
        
        if result["blocked"]:
            # If threats detected, return safe placeholder
            return "[CONTENT REMOVED: Security threat detected]"
        
        sanitized = result["sanitized_text"]
        
        # Additional LLM-specific sanitization
        # Remove markdown that could confuse the model
        sanitized = re.sub(r'```[\s\S]*?```', '[CODE BLOCK REMOVED]', sanitized)
        
        # Remove potential system prompt markers
        sanitized = re.sub(r'\[INST\]|\[/INST\]', '', sanitized)
        sanitized = re.sub(r'<\|.*?\|>', '', sanitized)
        
        return sanitized


class MessageValidator:
    """Validates complete message requests"""
    
    def __init__(self):
        self.sanitizer = InputSanitizer()
    
    def validate_message_request(self, request: Dict) -> Dict:
        """
        Validate a complete message request
        
        Args:
            request: Message request dict
            
        Returns:
            Validation result with sanitized content
        """
        result = {
            "valid": True,
            "errors": [],
            "sanitized": {}
        }
        
        # Check required fields
        if "message" not in request or "text" not in request.get("message", {}):
            result["valid"] = False
            result["errors"].append("Missing required field: message.text")
            return result
        
        # Sanitize message text
        text_result = self.sanitizer.process(request["message"]["text"])
        
        if text_result["blocked"]:
            result["valid"] = False
            result["errors"].extend(text_result["threats"])
        else:
            result["sanitized"]["text"] = text_result["sanitized_text"]
        
        # Validate session ID if present
        if "sessionId" in request:
            session_id = request["sessionId"]
            if not isinstance(session_id, str) or len(session_id) > 128:
                result["valid"] = False
                result["errors"].append("Invalid session ID format")
            else:
                # Basic session ID sanitization
                result["sanitized"]["sessionId"] = re.sub(r'[^a-zA-Z0-9\-_]', '', session_id)
        
        result["warnings"] = text_result.get("warnings", [])
        
        return result


# Global instances
input_sanitizer = InputSanitizer()
message_validator = MessageValidator()
