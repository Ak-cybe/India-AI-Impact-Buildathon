"""Security utilities for Agentic Honeypot API - Week 4"""

import re
import time
import hashlib
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from fastapi import HTTPException, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class RateLimitConfig(BaseModel):
    """Rate limiting configuration"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_limit: int = 10  # Max requests in 10 seconds
    block_duration_minutes: int = 15


class RateLimiter:
    """
    Rate limiter with multiple time windows
    
    Features:
    - Per-minute, per-hour, and burst limiting
    - IP-based and API-key-based tracking
    - Automatic cleanup of old entries
    - Blocklist for abusive clients
    """
    
    def __init__(self, config: RateLimitConfig = None):
        self.config = config or RateLimitConfig()
        
        # Request tracking: {identifier: [(timestamp, ...}]}
        self.request_log: Dict[str, List[float]] = defaultdict(list)
        
        # Blocklist: {identifier: unblock_timestamp}
        self.blocklist: Dict[str, float] = {}
        
        # Last cleanup timestamp
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes
    
    def _get_identifier(self, request: Request, api_key: str = None) -> str:
        """Get unique identifier for rate limiting"""
        # Use API key if available, otherwise use IP
        if api_key:
            return f"key:{hashlib.md5(api_key.encode()).hexdigest()[:16]}"
        
        # Get real IP (handle proxies)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        
        return f"ip:{ip}"
    
    def is_blocked(self, identifier: str) -> Tuple[bool, Optional[int]]:
        """Check if identifier is blocked"""
        if identifier in self.blocklist:
            unblock_time = self.blocklist[identifier]
            if time.time() < unblock_time:
                remaining = int(unblock_time - time.time())
                return True, remaining
            else:
                # Unblock
                del self.blocklist[identifier]
        return False, None
    
    def check_rate_limit(
        self,
        request: Request,
        api_key: str = None
    ) -> Tuple[bool, Dict]:
        """
        Check if request should be rate limited
        
        Returns:
            (is_allowed, details)
        """
        identifier = self._get_identifier(request, api_key)
        now = time.time()
        
        # Periodic cleanup
        if now - self.last_cleanup > self.cleanup_interval:
            self._cleanup()
        
        # Check blocklist
        is_blocked, remaining = self.is_blocked(identifier)
        if is_blocked:
            return False, {
                "error": "rate_limited",
                "reason": "too_many_requests",
                "retry_after": remaining,
                "identifier": identifier[:20]
            }
        
        # Get request history
        requests = self.request_log[identifier]
        
        # Clean old entries (keep last hour only)
        one_hour_ago = now - 3600
        requests = [t for t in requests if t > one_hour_ago]
        self.request_log[identifier] = requests
        
        # Check burst limit (10 seconds)
        ten_seconds_ago = now - 10
        recent_burst = sum(1 for t in requests if t > ten_seconds_ago)
        if recent_burst >= self.config.burst_limit:
            self._block(identifier)
            return False, {
                "error": "rate_limited",
                "reason": "burst_limit_exceeded",
                "limit": self.config.burst_limit,
                "window": "10s"
            }
        
        # Check per-minute limit
        one_minute_ago = now - 60
        recent_minute = sum(1 for t in requests if t > one_minute_ago)
        if recent_minute >= self.config.requests_per_minute:
            return False, {
                "error": "rate_limited",
                "reason": "minute_limit_exceeded",
                "limit": self.config.requests_per_minute,
                "retry_after": 60
            }
        
        # Check per-hour limit
        recent_hour = len(requests)
        if recent_hour >= self.config.requests_per_hour:
            return False, {
                "error": "rate_limited",
                "reason": "hour_limit_exceeded",
                "limit": self.config.requests_per_hour,
                "retry_after": 3600
            }
        
        # Log this request
        requests.append(now)
        self.request_log[identifier] = requests
        
        return True, {
            "allowed": True,
            "remaining_minute": self.config.requests_per_minute - recent_minute - 1,
            "remaining_hour": self.config.requests_per_hour - recent_hour - 1
        }
    
    def _block(self, identifier: str):
        """Block an identifier for configured duration"""
        unblock_time = time.time() + (self.config.block_duration_minutes * 60)
        self.blocklist[identifier] = unblock_time
        logger.warning(f"[RateLimiter] Blocked {identifier[:20]}... for {self.config.block_duration_minutes} minutes")
    
    def _cleanup(self):
        """Clean up old request logs and expired blocks"""
        now = time.time()
        one_hour_ago = now - 3600
        
        # Clean request logs
        for identifier in list(self.request_log.keys()):
            requests = [t for t in self.request_log[identifier] if t > one_hour_ago]
            if requests:
                self.request_log[identifier] = requests
            else:
                del self.request_log[identifier]
        
        # Clean expired blocks
        for identifier in list(self.blocklist.keys()):
            if self.blocklist[identifier] < now:
                del self.blocklist[identifier]
        
        self.last_cleanup = now
        logger.debug(f"[RateLimiter] Cleanup complete. {len(self.request_log)} tracked, {len(self.blocklist)} blocked")


class InputSanitizer:
    """
    Input sanitization and validation
    
    Features:
    - Injection attack prevention
    - XSS prevention
    - Size limits
    - Malicious pattern detection
    """
    
    # Dangerous patterns to detect
    INJECTION_PATTERNS = [
        # SQL injection
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|FROM|WHERE)\b.*[\;\-\-])',
        # Command injection
        r'([\|\;\&\`\$\(\)].*[\|\;\&\`\$\(\)])',
        # Path traversal
        r'(\.\./|\.\.\\|%2e%2e)',
        # LDAP injection
        r'(\(\||\)\||\)\&|\(\&)',
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>',
        r'<object[^>]*>',
    ]
    
    # Maximum field lengths
    MAX_LENGTHS = {
        "message": 10000,  # 10KB max message
        "sessionId": 100,
        "metadata": 5000,
        "field": 1000  # Default
    }
    
    def __init__(self):
        # Pre-compile patterns
        self.injection_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.INJECTION_PATTERNS
        ]
        self.xss_patterns = [
            re.compile(p, re.IGNORECASE | re.DOTALL) for p in self.XSS_PATTERNS
        ]
    
    def sanitize_string(self, value: str, field_name: str = "field") -> str:
        """
        Sanitize a string value
        
        Args:
            value: String to sanitize
            field_name: Name of field (for length limits)
            
        Returns:
            Sanitized string
        """
        if not value:
            return value
        
        # Enforce length limit
        max_len = self.MAX_LENGTHS.get(field_name, self.MAX_LENGTHS["field"])
        if len(value) > max_len:
            logger.warning(f"[Sanitizer] Truncating {field_name}: {len(value)} > {max_len}")
            value = value[:max_len]
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Don't strip other characters - we want natural language
        # Just escape potentially dangerous HTML
        value = value.replace('<', '&lt;').replace('>', '&gt;')
        
        return value
    
    def check_for_attacks(self, value: str) -> Tuple[bool, Optional[str]]:
        """
        Check string for attack patterns
        
        Returns:
            (is_safe, attack_type)
        """
        if not value:
            return True, None
        
        # Check injection patterns
        for pattern in self.injection_patterns:
            if pattern.search(value):
                return False, "injection_attempt"
        
        # Check XSS patterns (in original, unescaped value)
        for pattern in self.xss_patterns:
            if pattern.search(value):
                return False, "xss_attempt"
        
        return True, None
    
    def sanitize_request(self, data: Dict) -> Tuple[Dict, List[str]]:
        """
        Sanitize full request data
        
        Returns:
            (sanitized_data, warnings)
        """
        warnings = []
        sanitized = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                # Check for attacks first
                is_safe, attack_type = self.check_for_attacks(value)
                if not is_safe:
                    warnings.append(f"Suspicious pattern detected in {key}: {attack_type}")
                    logger.warning(f"[Sanitizer] Attack detected in {key}: {attack_type}")
                
                # Sanitize regardless
                sanitized[key] = self.sanitize_string(value, key)
                
            elif isinstance(value, dict):
                # Recursively sanitize dicts
                sanitized[key], sub_warnings = self.sanitize_request(value)
                warnings.extend(sub_warnings)
            else:
                sanitized[key] = value
        
        return sanitized, warnings


class KillSwitch:
    """
    Emergency kill switch for the honeypot
    
    Features:
    - Session termination
    - System pause
    - Audit logging
    - Manual override
    """
    
    def __init__(self):
        self.is_active = True
        self.pause_reason: Optional[str] = None
        self.pause_timestamp: Optional[datetime] = None
        self.killed_sessions: List[str] = []
    
    def pause_system(self, reason: str = "Manual pause") -> Dict:
        """Pause all honeypot operations"""
        self.is_active = False
        self.pause_reason = reason
        self.pause_timestamp = datetime.now()
        
        logger.warning(f"[KillSwitch] 🛑 SYSTEM PAUSED: {reason}")
        
        return {
            "status": "paused",
            "reason": reason,
            "timestamp": self.pause_timestamp.isoformat()
        }
    
    def resume_system(self) -> Dict:
        """Resume honeypot operations"""
        was_paused = not self.is_active
        pause_duration = None
        
        if was_paused and self.pause_timestamp:
            pause_duration = (datetime.now() - self.pause_timestamp).total_seconds()
        
        self.is_active = True
        self.pause_reason = None
        self.pause_timestamp = None
        
        logger.info(f"[KillSwitch] ✅ SYSTEM RESUMED after {pause_duration:.0f}s" if pause_duration else "[KillSwitch] ✅ SYSTEM RESUMED")
        
        return {
            "status": "active",
            "was_paused": was_paused,
            "pause_duration_seconds": pause_duration
        }
    
    def kill_session(self, session_id: str, reason: str = "Manual termination") -> Dict:
        """Immediately terminate a specific session"""
        self.killed_sessions.append(session_id)
        
        logger.warning(f"[KillSwitch] Session {session_id} terminated: {reason}")
        
        return {
            "session_id": session_id,
            "status": "terminated",
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
    
    def is_session_killed(self, session_id: str) -> bool:
        """Check if session has been killed"""
        return session_id in self.killed_sessions
    
    def get_status(self) -> Dict:
        """Get current kill switch status"""
        return {
            "system_active": self.is_active,
            "pause_reason": self.pause_reason,
            "pause_timestamp": self.pause_timestamp.isoformat() if self.pause_timestamp else None,
            "killed_sessions_count": len(self.killed_sessions)
        }


# Global instances
rate_limiter = RateLimiter()
input_sanitizer = InputSanitizer()
kill_switch = KillSwitch()
