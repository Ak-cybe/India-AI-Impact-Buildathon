"""Engagement Agent - Main agent for scammer engagement with full persona simulation"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime

from app.agents.engagement.persona import HoneypotPersona
from app.agents.engagement.temporal_manager import TemporalManager
from app.agents.engagement.state_machine import ConversationStateMachine
from app.agents.engagement.response_generator import ResponseGenerator
from app.config import settings


class EngagementAgent:
    """
    Complete honeypot engagement agent that simulates a believable human
    
    Components:
    - Persona: Static/dynamic identity attributes
    - Temporal Manager: Response timing and availability
    - State Machine: Conversation flow management
    - Response Generator: LLM-powered response generation
    
    Based on CHATTERBOX "Victim as a Service" research
    """
    
    def __init__(self, session_id: str, scam_type: str = None, platform: str = "sms"):
        """
        Initialize engagement agent for a session
        
        Args:
            session_id: Unique session identifier
            scam_type: Detected scam type (for persona selection)
            platform: Communication platform (sms, whatsapp, email)
        """
        self.session_id = session_id
        self.scam_type = scam_type
        self.platform = platform
        
        # Initialize components
        self.persona = HoneypotPersona(scam_type=scam_type)
        self.temporal_manager = TemporalManager(self.persona.persona_type)
        self.state_machine = ConversationStateMachine(
            session_id=session_id,
            max_turns=settings.max_conversation_turns
        )
        self.response_generator = ResponseGenerator()
        
        # Conversation history
        self.conversation_history: List[Dict] = []
        
        # Intelligence extracted
        self.intelligence_items: List[Dict] = []
        
        # Session metadata
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        
        print(f"[EngagementAgent] Initialized for session {session_id}")
        print(f"  Persona: {self.persona.get_name()} ({self.persona.persona_type})")
        print(f"  Platform: {platform}")
    
    async def process_message(
        self, 
        scammer_message: str,
        metadata: Dict = None,
        apply_delay: bool = True
    ) -> Dict:
        """
        Process incoming scammer message and generate response
        
        Args:
            scammer_message: Message from scammer
            metadata: Message metadata (timestamp, channel, etc.)
            apply_delay: Whether to apply realistic response delay
            
        Returns:
            Dict with response and session status
        """
        print(f"\n[EngagementAgent] Processing message for session {self.session_id}")
        print(f"  State: {self.state_machine.get_current_state().value}")
        print(f"  Turn: {self.state_machine.turn_count}")
        
        # Check if persona is available (temporal awareness)
        is_available, availability_reason = self.temporal_manager.is_available()
        if not is_available:
            print(f"  [Temporal] Not available: {availability_reason}")
            return {
                "response": None,
                "session_active": True,
                "reason": availability_reason,
                "delay_until_available": True
            }
        
        # Check platform constraints
        platform_constraints = self.temporal_manager.get_platform_constraints(self.platform)
        
        # Check if should take a break (realistic human behavior)
        should_break, break_reason = self.temporal_manager.should_take_break(
            self.state_machine.turn_count
        )
        if should_break:
            print(f"  [Temporal] Taking break: {break_reason}")
            # Record the break in history
            self.conversation_history.append({
                "role": "scammer",
                "message": scammer_message,
                "timestamp": datetime.now().isoformat()
            })
            self.conversation_history.append({
                "role": "agent",
                "message": break_reason,
                "timestamp": datetime.now().isoformat(),
                "is_break": True
            })
            return {
                "response": break_reason,
                "session_active": True,
                "is_break": True
            }
        
        # Apply response delay (critical for believability!)
        if apply_delay:
            delay = self.temporal_manager.calculate_response_delay(len(scammer_message))
            print(f"  [Temporal] Response delay: {delay:.1f}s")
            # In production, this is where we'd actually wait
            # For testing, we just log it
            # await asyncio.sleep(delay)
        
        # Generate response using LLM
        response = await self.response_generator.generate_response(
            scammer_message=scammer_message,
            persona=self.persona,
            state_machine=self.state_machine,
            conversation_history=self.conversation_history[-10:]  # Last 10 turns for context
        )
        
        # Extract intelligence from scammer's message
        new_intelligence = self._extract_intelligence(scammer_message)
        if new_intelligence:
            self.intelligence_items.extend(new_intelligence)
            print(f"  [Intel] Extracted {len(new_intelligence)} items")
        
        # Record turn in state machine
        self.state_machine.record_turn(
            scammer_message=scammer_message,
            agent_response=response,
            intelligence_extracted=new_intelligence
        )
        
        # Update conversation history
        self.conversation_history.append({
            "role": "scammer",
            "message": scammer_message,
            "timestamp": datetime.now().isoformat()
        })
        self.conversation_history.append({
            "role": "agent",
            "message": response,
            "timestamp": datetime.now().isoformat(),
            "state": self.state_machine.get_current_state().value
        })
        
        # Update last activity
        self.last_activity = datetime.now()
        
        # Check if session should end
        is_complete = self.state_machine.is_session_complete()
        
        # Enforce platform constraints (e.g., SMS length limit)
        if len(response) > platform_constraints.get("max_length", 160):
            response = response[:platform_constraints["max_length"] - 3] + "..."
        
        return {
            "response": response,
            "session_active": not is_complete,
            "current_state": self.state_machine.get_current_state().value,
            "turn_count": self.state_machine.turn_count,
            "intelligence_count": len(self.intelligence_items)
        }
    
    def _extract_intelligence(self, message: str) -> List[Dict]:
        """
        Extract intelligence from scammer's message
        
        Args:
            message: Scammer's message text
            
        Returns:
            List of extracted intelligence items
        """
        import re
        
        intelligence = []
        timestamp = datetime.now().isoformat()
        
        # UPI ID pattern
        upi_pattern = r'\b[\w\.-]+@[\w\.-]+\b'
        upi_matches = re.findall(upi_pattern, message)
        for upi in upi_matches:
            if '@' in upi and any(p in upi for p in ['ybl', 'paytm', 'upi', 'okaxis', 'ibl']):
                intelligence.append({
                    "type": "upi_id",
                    "value": upi,
                    "confidence": 0.9,
                    "timestamp": timestamp
                })
        
        # Phone number pattern (Indian)
        phone_pattern = r'(\+91[-\s]?)?[6-9]\d{9}'
        phone_matches = re.findall(phone_pattern, message)
        for phone in phone_matches:
            if isinstance(phone, tuple):
                phone = ''.join(phone)
            intelligence.append({
                "type": "phone_number",
                "value": phone.strip(),
                "confidence": 0.85,
                "timestamp": timestamp
            })
        
        # Bank account pattern
        account_pattern = r'\b\d{9,18}\b'
        account_matches = re.findall(account_pattern, message)
        for acc in account_matches:
            if len(acc) >= 9:
                intelligence.append({
                    "type": "bank_account",
                    "value": acc,
                    "confidence": 0.7,
                    "timestamp": timestamp
                })
        
        # URL pattern
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        url_matches = re.findall(url_pattern, message)
        for url in url_matches:
            intelligence.append({
                "type": "url",
                "value": url,
                "confidence": 0.95,
                "timestamp": timestamp
            })
        
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_matches = re.findall(email_pattern, message)
        for email in email_matches:
            if not any(p in email for p in ['ybl', 'paytm', 'upi']):  # Exclude UPI IDs
                intelligence.append({
                    "type": "email",
                    "value": email,
                    "confidence": 0.9,
                    "timestamp": timestamp
                })
        
        return intelligence
    
    def get_session_report(self) -> Dict:
        """Get comprehensive session report"""
        return {
            "session_id": self.session_id,
            "scam_type": self.scam_type,
            "persona": {
                "name": self.persona.get_name(),
                "type": self.persona.persona_type,
                "age": self.persona.get_age()
            },
            "platform": self.platform,
            "state_summary": self.state_machine.get_session_summary(),
            "intelligence": {
                "count": len(self.intelligence_items),
                "items": self.intelligence_items
            },
            "conversation": {
                "total_turns": len(self.conversation_history) // 2,
                "history": self.conversation_history
            },
            "timing": {
                "created_at": self.created_at.isoformat(),
                "last_activity": self.last_activity.isoformat(),
                "duration_seconds": (self.last_activity - self.created_at).total_seconds()
            }
        }
    
    def get_final_callback_payload(self) -> Dict:
        """
        Get payload for final callback to evaluation endpoint
        
        Matches required format from hackathon spec
        """
        return {
            "sessionId": self.session_id,
            "scamType": self.scam_type or "generic_scam",
            "intelligenceGathered": self.intelligence_items,
            "conversationTranscript": [
                {"role": turn["role"], "message": turn["message"]}
                for turn in self.conversation_history
            ],
            "confidence": 0.85,  # Aggregate from analysis
            "totalTurns": self.state_machine.turn_count,
            "timestamp": datetime.now().isoformat()
        }
