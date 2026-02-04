"""Session Manager - Handles multiple concurrent honeypot sessions"""

from typing import Dict, Optional
from datetime import datetime, timedelta
import asyncio
from app.agents.engagement.engagement_agent import EngagementAgent


class SessionManager:
    """
    Manages multiple honeypot sessions concurrently
    
    Features:
    - Session creation and retrieval
    - Automatic session cleanup (timeout)
    - Session state persistence (in-memory, can be extended to Redis)
    """
    
    def __init__(self, session_timeout_minutes: int = 30):
        """
        Initialize session manager
        
        Args:
            session_timeout_minutes: Minutes of inactivity before session expires
        """
        self.sessions: Dict[str, EngagementAgent] = {}
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        
        # Completed sessions (for callback/reporting)
        self.completed_sessions: Dict[str, Dict] = {}
        
        print(f"[SessionManager] Initialized (timeout: {session_timeout_minutes} min)")
    
    def create_session(
        self, 
        session_id: str, 
        scam_type: str = None,
        platform: str = "sms"
    ) -> EngagementAgent:
        """
        Create a new engagement session
        
        Args:
            session_id: Unique session identifier
            scam_type: Detected scam type
            platform: Communication platform
            
        Returns:
            New EngagementAgent instance
        """
        # Check if session already exists
        if session_id in self.sessions:
            print(f"[SessionManager] Session {session_id} already exists, returning existing")
            return self.sessions[session_id]
        
        # Create new agent
        agent = EngagementAgent(
            session_id=session_id,
            scam_type=scam_type,
            platform=platform
        )
        
        self.sessions[session_id] = agent
        print(f"[SessionManager] Created session {session_id} (total: {len(self.sessions)})")
        
        return agent
    
    def get_session(self, session_id: str) -> Optional[EngagementAgent]:
        """
        Get existing session by ID
        
        Args:
            session_id: Session to retrieve
            
        Returns:
            EngagementAgent if exists, None otherwise
        """
        return self.sessions.get(session_id)
    
    def get_or_create_session(
        self,
        session_id: str,
        scam_type: str = None,
        platform: str = "sms"
    ) -> EngagementAgent:
        """
        Get existing session or create new one
        
        Args:
            session_id: Session identifier
            scam_type: Scam type (for new sessions)
            platform: Platform (for new sessions)
            
        Returns:
            EngagementAgent instance
        """
        existing = self.get_session(session_id)
        if existing:
            return existing
        return self.create_session(session_id, scam_type, platform)
    
    def complete_session(self, session_id: str) -> Dict:
        """
        Mark session as complete and move to completed store
        
        Args:
            session_id: Session to complete
            
        Returns:
            Final session report
        """
        agent = self.sessions.get(session_id)
        if not agent:
            return {"error": f"Session {session_id} not found"}
        
        # Get final report
        report = agent.get_session_report()
        
        # Get callback payload
        callback_payload = agent.get_final_callback_payload()
        report["callback_payload"] = callback_payload
        
        # Move to completed
        self.completed_sessions[session_id] = report
        
        # Remove from active
        del self.sessions[session_id]
        
        print(f"[SessionManager] Completed session {session_id}")
        print(f"  Intelligence items: {len(agent.intelligence_items)}")
        print(f"  Total turns: {agent.state_machine.turn_count}")
        
        return report
    
    def cleanup_expired_sessions(self) -> int:
        """
        Remove sessions that have exceeded timeout
        
        Returns:
            Number of sessions cleaned up
        """
        now = datetime.now()
        expired = []
        
        for session_id, agent in self.sessions.items():
            if now - agent.last_activity > self.session_timeout:
                expired.append(session_id)
        
        for session_id in expired:
            # Complete the session before removing
            self.complete_session(session_id)
        
        if expired:
            print(f"[SessionManager] Cleaned up {len(expired)} expired sessions")
        
        return len(expired)
    
    def get_active_session_count(self) -> int:
        """Get count of active sessions"""
        return len(self.sessions)
    
    def get_completed_session_count(self) -> int:
        """Get count of completed sessions"""
        return len(self.completed_sessions)
    
    def get_session_summary(self, session_id: str) -> Optional[Dict]:
        """Get quick summary of a session"""
        agent = self.sessions.get(session_id)
        if not agent:
            return self.completed_sessions.get(session_id)
        
        return {
            "session_id": session_id,
            "status": "active",
            "persona": agent.persona.get_name(),
            "turn_count": agent.state_machine.turn_count,
            "intelligence_count": len(agent.intelligence_items),
            "current_state": agent.state_machine.get_current_state().value
        }
    
    def get_all_sessions_summary(self) -> Dict:
        """Get summary of all sessions"""
        active = [
            {
                "session_id": sid,
                "persona": agent.persona.get_name(),
                "turns": agent.state_machine.turn_count,
                "intel": len(agent.intelligence_items),
                "state": agent.state_machine.get_current_state().value
            }
            for sid, agent in self.sessions.items()
        ]
        
        return {
            "active_count": len(self.sessions),
            "completed_count": len(self.completed_sessions),
            "active_sessions": active
        }


# Global session manager instance
session_manager = SessionManager()
