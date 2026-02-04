"""Rate Limiter - Protection against abuse and DoS"""

import time
from typing import Dict, Optional
from collections import defaultdict
import asyncio


class RateLimiter:
    """
    Token bucket rate limiter for API protection
    
    Features:
    - Per-IP rate limiting
    - Per-session rate limiting  
    - Configurable limits
    - Automatic cleanup of old entries
    """
    
    def __init__(
        self,
        requests_per_minute: int = 30,
        requests_per_hour: int = 500,
        burst_limit: int = 10
    ):
        """
        Initialize rate limiter
        
        Args:
            requests_per_minute: Max requests per minute per client
            requests_per_hour: Max requests per hour per client
            burst_limit: Max burst requests in quick succession
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_limit = burst_limit
        
        # Track requests per client
        self.minute_buckets: Dict[str, list] = defaultdict(list)
        self.hour_buckets: Dict[str, list] = defaultdict(list)
        
        # Track blocked clients
        self.blocked: Dict[str, float] = {}
        
        # Cleanup interval
        self._last_cleanup = time.time()
        self._cleanup_interval = 60  # seconds
    
    def is_allowed(self, client_id: str) -> tuple:
        """
        Check if request from client is allowed
        
        Args:
            client_id: Unique client identifier (IP or session ID)
            
        Returns:
            (is_allowed, reason, retry_after_seconds)
        """
        current_time = time.time()
        
        # Periodic cleanup
        if current_time - self._last_cleanup > self._cleanup_interval:
            self._cleanup()
        
        # Check if blocked
        if client_id in self.blocked:
            unblock_time = self.blocked[client_id]
            if current_time < unblock_time:
                retry_after = int(unblock_time - current_time)
                return False, "temporarily_blocked", retry_after
            else:
                del self.blocked[client_id]
        
        # Clean old entries for this client
        minute_ago = current_time - 60
        hour_ago = current_time - 3600
        
        self.minute_buckets[client_id] = [
            t for t in self.minute_buckets[client_id] if t > minute_ago
        ]
        self.hour_buckets[client_id] = [
            t for t in self.hour_buckets[client_id] if t > hour_ago
        ]
        
        # Check minute limit
        if len(self.minute_buckets[client_id]) >= self.requests_per_minute:
            oldest = min(self.minute_buckets[client_id])
            retry_after = int(60 - (current_time - oldest))
            return False, "minute_limit_exceeded", max(1, retry_after)
        
        # Check hour limit
        if len(self.hour_buckets[client_id]) >= self.requests_per_hour:
            oldest = min(self.hour_buckets[client_id])
            retry_after = int(3600 - (current_time - oldest))
            return False, "hour_limit_exceeded", max(1, retry_after)
        
        # Check burst (last 5 seconds)
        five_seconds_ago = current_time - 5
        recent_requests = [
            t for t in self.minute_buckets[client_id] if t > five_seconds_ago
        ]
        if len(recent_requests) >= self.burst_limit:
            # Burst detected - block for 30 seconds
            self.blocked[client_id] = current_time + 30
            return False, "burst_limit_exceeded", 30
        
        # Record this request
        self.minute_buckets[client_id].append(current_time)
        self.hour_buckets[client_id].append(current_time)
        
        return True, "allowed", 0
    
    def block_client(self, client_id: str, duration_seconds: int = 300):
        """
        Manually block a client
        
        Args:
            client_id: Client to block
            duration_seconds: Block duration (default 5 minutes)
        """
        self.blocked[client_id] = time.time() + duration_seconds
    
    def unblock_client(self, client_id: str):
        """Manually unblock a client"""
        if client_id in self.blocked:
            del self.blocked[client_id]
    
    def get_client_stats(self, client_id: str) -> Dict:
        """Get rate limit stats for a client"""
        current_time = time.time()
        minute_ago = current_time - 60
        hour_ago = current_time - 3600
        
        # Clean and count
        minute_requests = len([
            t for t in self.minute_buckets.get(client_id, []) if t > minute_ago
        ])
        hour_requests = len([
            t for t in self.hour_buckets.get(client_id, []) if t > hour_ago
        ])
        
        return {
            "client_id": client_id,
            "requests_last_minute": minute_requests,
            "requests_last_hour": hour_requests,
            "minute_limit": self.requests_per_minute,
            "hour_limit": self.requests_per_hour,
            "is_blocked": client_id in self.blocked,
            "blocked_until": self.blocked.get(client_id)
        }
    
    def _cleanup(self):
        """Clean up old entries"""
        current_time = time.time()
        hour_ago = current_time - 3600
        
        # Remove old entries
        for client_id in list(self.minute_buckets.keys()):
            self.minute_buckets[client_id] = [
                t for t in self.minute_buckets[client_id] if t > hour_ago
            ]
            if not self.minute_buckets[client_id]:
                del self.minute_buckets[client_id]
        
        for client_id in list(self.hour_buckets.keys()):
            self.hour_buckets[client_id] = [
                t for t in self.hour_buckets[client_id] if t > hour_ago
            ]
            if not self.hour_buckets[client_id]:
                del self.hour_buckets[client_id]
        
        # Remove expired blocks
        for client_id in list(self.blocked.keys()):
            if self.blocked[client_id] < current_time:
                del self.blocked[client_id]
        
        self._last_cleanup = current_time


class SessionRateLimiter:
    """Per-session rate limiter for conversation flow"""
    
    def __init__(self, min_interval_seconds: float = 2.0):
        """
        Args:
            min_interval_seconds: Minimum time between messages in a session
        """
        self.min_interval = min_interval_seconds
        self.last_message_time: Dict[str, float] = {}
    
    def check_session_rate(self, session_id: str) -> tuple:
        """
        Check if session is sending messages too fast
        
        Returns:
            (is_allowed, wait_seconds)
        """
        current_time = time.time()
        
        if session_id not in self.last_message_time:
            self.last_message_time[session_id] = current_time
            return True, 0
        
        elapsed = current_time - self.last_message_time[session_id]
        
        if elapsed < self.min_interval:
            wait = self.min_interval - elapsed
            return False, wait
        
        self.last_message_time[session_id] = current_time
        return True, 0
    
    def cleanup_old_sessions(self, max_age_seconds: int = 3600):
        """Remove old session entries"""
        current_time = time.time()
        cutoff = current_time - max_age_seconds
        
        for session_id in list(self.last_message_time.keys()):
            if self.last_message_time[session_id] < cutoff:
                del self.last_message_time[session_id]


# Global rate limiter instances
rate_limiter = RateLimiter()
session_rate_limiter = SessionRateLimiter()
