"""Temporal Manager - Timezone awareness and response timing for believable personas"""

from datetime import datetime, time
from typing import Dict, Optional, Tuple
import random
import asyncio


class TemporalManager:
    """
    Manages temporal aspects of persona behavior:
    - Timezone-based availability (personas need to "sleep")
    - Response latency jitter (avoid instant bot-like responses)
    - Daily routine patterns
    
    Based on CHATTERBOX research: AI that responds at 3 AM is suspicious!
    """
    
    # Indian timezone offset from UTC
    IST_OFFSET_HOURS = 5.5
    
    # Default availability windows (24-hour format)
    AVAILABILITY_PROFILES = {
        "elderly_retired": {
            "wake_time": time(5, 30),   # Wake up at 5:30 AM
            "sleep_time": time(21, 30),  # Sleep at 9:30 PM
            "lunch_break": (time(12, 0), time(13, 0)),  # Less responsive during lunch
            "evening_puja": (time(18, 0), time(19, 0)),  # Evening prayer time
            "response_multiplier": 1.5  # Slower responses (older, less techy)
        },
        "middle_aged_business": {
            "wake_time": time(6, 30),
            "sleep_time": time(23, 0),
            "lunch_break": (time(13, 0), time(14, 0)),
            "busy_hours": [(time(10, 0), time(12, 0)), (time(15, 0), time(18, 0))],
            "response_multiplier": 1.0  # Normal responses
        },
        "young_professional": {
            "wake_time": time(7, 30),
            "sleep_time": time(0, 30),  # Night owl
            "lunch_break": (time(13, 0), time(14, 0)),
            "work_meeting_hours": [(time(10, 0), time(11, 0)), (time(14, 0), time(15, 0))],
            "response_multiplier": 0.7  # Faster responses (tech-savvy)
        }
    }
    
    def __init__(self, persona_type: str = "middle_aged_business"):
        """
        Initialize temporal manager for persona
        
        Args:
            persona_type: Type of persona (affects availability patterns)
        """
        self.persona_type = persona_type
        self.profile = self.AVAILABILITY_PROFILES.get(
            persona_type, 
            self.AVAILABILITY_PROFILES["middle_aged_business"]
        )
        
        # Base response delay range (seconds)
        self.min_delay = 10
        self.max_delay = 90
    
    def is_available(self, current_time: datetime = None) -> Tuple[bool, str]:
        """
        Check if persona is available to respond
        
        Args:
            current_time: Time to check (defaults to now in IST)
            
        Returns:
            (is_available, reason)
        """
        if current_time is None:
            current_time = datetime.now()
        
        current_hour_minute = current_time.time()
        
        wake_time = self.profile["wake_time"]
        sleep_time = self.profile["sleep_time"]
        
        # Check if sleeping (handles midnight crossover)
        if sleep_time > wake_time:
            # Normal case: sleep after midnight or before wake
            is_sleeping = current_hour_minute < wake_time or current_hour_minute >= sleep_time
        else:
            # Night owl case: sleep time is past midnight
            is_sleeping = current_hour_minute >= sleep_time and current_hour_minute < wake_time
        
        if is_sleeping:
            return False, f"Persona is sleeping (sleep: {sleep_time}, wake: {wake_time})"
        
        # Check lunch break
        lunch_break = self.profile.get("lunch_break")
        if lunch_break:
            if lunch_break[0] <= current_hour_minute <= lunch_break[1]:
                # During lunch - 50% chance of delayed response
                if random.random() < 0.5:
                    return True, "During lunch break - may be slower"
        
        # Check busy hours (for applicable personas)
        busy_hours = self.profile.get("busy_hours", [])
        for start, end in busy_hours:
            if start <= current_hour_minute <= end:
                # During busy hours - 30% chance of no response
                if random.random() < 0.3:
                    return False, f"Busy with work ({start} - {end})"
        
        return True, "Available"
    
    def calculate_response_delay(self, message_length: int = 100) -> float:
        """
        Calculate human-like response delay
        
        Factors:
        - Base random delay (10-90 seconds)
        - Message length (reading time)
        - Persona multiplier (tech-savviness)
        - Random "distraction" delays
        
        Args:
            message_length: Length of incoming message (affects "reading time")
            
        Returns:
            Delay in seconds
        """
        # Base delay
        base_delay = random.uniform(self.min_delay, self.max_delay)
        
        # Reading time: ~200ms per character for slow reader, ~50ms for fast
        reading_multiplier = {
            "elderly_retired": 0.2,
            "middle_aged_business": 0.1,
            "young_professional": 0.05
        }.get(self.persona_type, 0.1)
        
        reading_time = message_length * reading_multiplier
        
        # Apply persona multiplier
        persona_multiplier = self.profile.get("response_multiplier", 1.0)
        
        # Calculate base response time
        delay = (base_delay + reading_time) * persona_multiplier
        
        # Add random "distraction" delays (15% chance)
        if random.random() < 0.15:
            distraction_delay = random.uniform(60, 300)  # 1-5 minutes
            delay += distraction_delay
        
        # Add typing time (persona needs time to "type" response)
        # Assume ~5-15 words per response, ~1-3 seconds per word
        typing_time = random.uniform(10, 45)
        delay += typing_time
        
        # Ensure minimum of 2 seconds (never instant!)
        return max(delay, 2.0)
    
    async def apply_response_delay(self, message_length: int = 100):
        """
        Async method to actually wait for response delay
        
        Args:
            message_length: Length of incoming message
        """
        delay = self.calculate_response_delay(message_length)
        print(f"[TemporalManager] Applying {delay:.1f}s response delay...")
        await asyncio.sleep(delay)
    
    def get_greeting_for_time(self, current_time: datetime = None) -> str:
        """
        Get appropriate greeting based on time of day
        
        Args:
            current_time: Time to check
            
        Returns:
            Appropriate greeting in Hinglish
        """
        if current_time is None:
            current_time = datetime.now()
        
        hour = current_time.hour
        
        if 5 <= hour < 12:
            greetings = ["Namaste", "Good morning", "Suprabhat"]
        elif 12 <= hour < 17:
            greetings = ["Namaskar", "Hello", "Ji"]
        elif 17 <= hour < 21:
            greetings = ["Shubh sandhya", "Good evening", "Namaskar"]
        else:
            greetings = ["Ji", "Hello", "Haan"]
        
        return random.choice(greetings)
    
    def should_take_break(self, conversation_turns: int) -> Tuple[bool, str]:
        """
        Determine if persona should take a break (realistic human behavior)
        
        Args:
            conversation_turns: Number of turns so far
            
        Returns:
            (should_break, reason_to_give)
        """
        # After 5 turns, 10% chance of break
        if conversation_turns >= 5 and random.random() < 0.10:
            reasons = [
                "Ek minute, chai bana rahi hoon",
                "Wait, door pe koi aaya hai",
                "Phone pe dusra call aa raha hai",
                "Abhi busy hoon, thodi der mein reply karti hoon"
            ]
            return True, random.choice(reasons)
        
        # After 10 turns, 20% chance of break
        if conversation_turns >= 10 and random.random() < 0.20:
            reasons = [
                "Mujhe bahar jaana hai, baad mein baat karte hain",
                "Khana banana hai, thodi der mein milte hain",
                "Koi aa gaya ghar pe, message baad mein",
            ]
            return True, random.choice(reasons)
        
        return False, ""
    
    def get_platform_constraints(self, platform: str) -> Dict:
        """
        Get platform-specific constraints
        
        Args:
            platform: Communication platform (sms, whatsapp, email)
            
        Returns:
            Dict of constraints
        """
        constraints = {
            "sms": {
                "max_length": 160,
                "can_send_images": False,
                "can_send_audio": False,
                "can_send_links": True,
                "supports_formatting": False
            },
            "whatsapp": {
                "max_length": 4096,
                "can_send_images": True,
                "can_send_audio": True,
                "can_send_links": True,
                "supports_formatting": True
            },
            "email": {
                "max_length": 65536,
                "can_send_images": True,
                "can_send_audio": False,
                "can_send_links": True,
                "supports_formatting": True
            }
        }
        
        return constraints.get(platform, constraints["sms"])
