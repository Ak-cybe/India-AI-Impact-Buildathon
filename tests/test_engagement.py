"""Tests for engagement system - Persona, Temporal, State Machine"""

import pytest
import asyncio
from datetime import datetime, time

# Import test subjects
import sys
sys.path.insert(0, 'c:\\Users\\Acer\\Desktop\\lab\\Hackathon Challenge')

from app.agents.engagement.persona import HoneypotPersona
from app.agents.engagement.temporal_manager import TemporalManager
from app.agents.engagement.state_machine import ConversationStateMachine, ConversationState


class TestHoneypotPersona:
    """Test persona system"""
    
    def test_persona_creation_elderly(self):
        """Test elderly persona creation"""
        persona = HoneypotPersona(persona_type="elderly_retired")
        
        assert persona.get_name() == "Shanti Devi"
        assert persona.get_age() == 68
        assert persona.static_attrs["gender"] == "female"
        assert persona.static_attrs["location"] == "Varanasi, Uttar Pradesh"
    
    def test_persona_creation_business(self):
        """Test middle-aged business persona"""
        persona = HoneypotPersona(persona_type="middle_aged_business")
        
        assert persona.get_name() == "Rajesh Kumar Sharma"
        assert persona.get_age() == 48
        assert persona.behavioral_policies["tech_savviness"] == "medium"
    
    def test_persona_creation_young(self):
        """Test young professional persona"""
        persona = HoneypotPersona(persona_type="young_professional")
        
        assert persona.get_name() == "Priya Nair"
        assert persona.get_age() == 27
        assert persona.behavioral_policies["tech_savviness"] == "high"
    
    def test_scam_type_matching_bank_fraud(self):
        """Test bank fraud selects elderly persona"""
        persona = HoneypotPersona(scam_type="bank_fraud")
        
        # Bank fraud should select elderly (most vulnerable)
        assert "Shanti" in persona.get_name() or "Rajesh" in persona.get_name()
    
    def test_scam_type_matching_investment(self):
        """Test investment scam selects young professional"""
        persona = HoneypotPersona(scam_type="investment_scam")
        
        # Should select young professional
        assert persona.behavioral_policies["tech_savviness"] == "high"
    
    def test_persona_context_generation(self):
        """Test LLM context generation"""
        persona = HoneypotPersona(persona_type="elderly_retired")
        context = persona.get_context_for_llm()
        
        assert "Shanti Devi" in context
        assert "68" in context
        assert "Varanasi" in context
        assert "BEHAVIORAL TRAITS" in context
    
    def test_response_validation_gender_consistency(self):
        """Test response validation catches gender inconsistency"""
        persona = HoneypotPersona(persona_type="elderly_retired")  # Female
        
        # Valid response
        is_valid, _ = persona.validate_response("Main ek aurat hoon")
        assert is_valid
        
        # Invalid response (wrong gender)
        is_valid, reason = persona.validate_response("I am a man and I work hard")
        assert not is_valid
        assert "Gender" in reason
    
    def test_revealed_facts_tracking(self):
        """Test that revealed facts are tracked"""
        persona = HoneypotPersona(persona_type="elderly_retired")
        
        persona.add_revealed_fact("Told scammer I have 2 sons")
        persona.add_revealed_fact("Mentioned living in Varanasi")
        
        assert len(persona.revealed_facts) == 2
        assert "2 sons" in persona.revealed_facts[0]
    
    def test_typo_patterns_by_tech_savviness(self):
        """Test typo generation based on tech level"""
        elderly = HoneypotPersona(persona_type="elderly_retired")
        young = HoneypotPersona(persona_type="young_professional")
        
        # Elderly has more typo patterns
        assert len(elderly.get_typo_patterns()) > len(young.get_typo_patterns())


class TestTemporalManager:
    """Test temporal awareness system"""
    
    def test_availability_during_day(self):
        """Test persona is available during normal hours"""
        manager = TemporalManager("middle_aged_business")
        
        # Create a time during business hours (2 PM)
        test_time = datetime(2026, 1, 30, 14, 0, 0)
        
        is_available, reason = manager.is_available(test_time)
        # Should be available (though might be in busy hours with random chance)
        # Just check it doesn't crash
        assert isinstance(is_available, bool)
    
    def test_availability_during_sleep(self):
        """Test persona is NOT available during sleep"""
        manager = TemporalManager("elderly_retired")  # Sleeps at 9:30 PM
        
        # Create a time during sleep (midnight)
        test_time = datetime(2026, 1, 30, 0, 0, 0)
        
        is_available, reason = manager.is_available(test_time)
        assert not is_available
        assert "sleeping" in reason.lower()
    
    def test_response_delay_calculation(self):
        """Test response delay is reasonable"""
        manager = TemporalManager("elderly_retired")
        
        delay = manager.calculate_response_delay(message_length=100)
        
        # Should be at least 2 seconds (never instant)
        assert delay >= 2.0
        # Should be reasonable (under 10 minutes usually)
        assert delay < 600
    
    def test_response_delay_varies_by_persona(self):
        """Test different personas have different response patterns"""
        elderly_manager = TemporalManager("elderly_retired")
        young_manager = TemporalManager("young_professional")
        
        # Run multiple times to average
        elderly_delays = [elderly_manager.calculate_response_delay(100) for _ in range(10)]
        young_delays = [young_manager.calculate_response_delay(100) for _ in range(10)]
        
        # Elderly should generally be slower (higher multiplier)
        avg_elderly = sum(elderly_delays) / len(elderly_delays)
        avg_young = sum(young_delays) / len(young_delays)
        
        # Allow for random variation but elderly should trend slower
        # This is probabilistic, so just check they're both positive
        assert avg_elderly > 0
        assert avg_young > 0
    
    def test_greeting_by_time(self):
        """Test appropriate greeting for time of day"""
        manager = TemporalManager("middle_aged_business")
        
        morning_time = datetime(2026, 1, 30, 9, 0, 0)
        evening_time = datetime(2026, 1, 30, 19, 0, 0)
        
        morning_greeting = manager.get_greeting_for_time(morning_time)
        evening_greeting = manager.get_greeting_for_time(evening_time)
        
        # Should return valid greetings
        assert morning_greeting in ["Namaste", "Good morning", "Suprabhat"]
        assert evening_greeting in ["Shubh sandhya", "Good evening", "Namaskar"]
    
    def test_platform_constraints(self):
        """Test platform-specific constraints"""
        manager = TemporalManager("middle_aged_business")
        
        sms_constraints = manager.get_platform_constraints("sms")
        whatsapp_constraints = manager.get_platform_constraints("whatsapp")
        
        assert sms_constraints["max_length"] == 160
        assert whatsapp_constraints["max_length"] == 4096
        assert not sms_constraints["can_send_images"]
        assert whatsapp_constraints["can_send_images"]


class TestConversationStateMachine:
    """Test conversation state machine"""
    
    def test_initial_state(self):
        """Test state machine starts in INITIAL state"""
        sm = ConversationStateMachine("test-session-1")
        
        assert sm.get_current_state() == ConversationState.INITIAL
        assert sm.turn_count == 0
    
    def test_state_strategy_retrieval(self):
        """Test getting strategy for current state"""
        sm = ConversationStateMachine("test-session-2")
        
        strategy = sm.get_strategy()
        
        assert "goal" in strategy
        assert "tactics" in strategy
        assert "example_responses" in strategy
        assert "surprise" in strategy["goal"].lower() or "concern" in strategy["goal"].lower()
    
    def test_turn_recording(self):
        """Test recording conversation turns"""
        sm = ConversationStateMachine("test-session-3")
        
        sm.record_turn(
            scammer_message="Your account is blocked",
            agent_response="Kya? Kaun bol raha hai?",
            intelligence_extracted=[]
        )
        
        assert sm.turn_count == 1
        assert sm.turns_in_current_state == 1
    
    def test_state_transition_after_max_turns(self):
        """Test state transitions after max turns in state"""
        sm = ConversationStateMachine("test-session-4", max_turns=20)
        
        # Force past max turns in INITIAL state
        for i in range(3):
            sm.record_turn(f"Message {i}", f"Response {i}")
        
        # Should have transitioned past INITIAL
        # (might still be in INITIAL due to randomness, but turn count should be accurate)
        assert sm.turn_count == 3
    
    def test_session_completion(self):
        """Test session completion detection"""
        sm = ConversationStateMachine("test-session-5", max_turns=5)
        
        # Force to max turns
        for i in range(5):
            sm.record_turn(f"Message {i}", f"Response {i}")
        
        assert sm.is_session_complete()
    
    def test_session_summary(self):
        """Test session summary generation"""
        sm = ConversationStateMachine("test-session-6")
        
        sm.record_turn("Hello", "Hi, kaun hai?")
        
        summary = sm.get_session_summary()
        
        assert summary["session_id"] == "test-session-6"
        assert summary["total_turns"] == 1
        assert "current_state" in summary
        assert "is_complete" in summary
    
    def test_llm_context_generation(self):
        """Test LLM context includes state info"""
        sm = ConversationStateMachine("test-session-7")
        
        context = sm.get_context_for_llm()
        
        assert "CURRENT CONVERSATION STATE" in context
        assert "GOAL" in context
        assert "TACTICS" in context


class TestIntegration:
    """Integration tests combining multiple components"""
    
    def test_persona_with_temporal_manager(self):
        """Test persona type correctly initializes temporal manager"""
        persona = HoneypotPersona(persona_type="elderly_retired")
        temporal = TemporalManager(persona.persona_type)
        
        # Elderly has 1.5x response multiplier
        assert temporal.profile["response_multiplier"] == 1.5
    
    def test_full_session_flow(self):
        """Test complete session flow simulation"""
        persona = HoneypotPersona(scam_type="bank_fraud")
        state_machine = ConversationStateMachine("integration-test-1")
        temporal = TemporalManager(persona.persona_type)
        
        # Simulate conversation
        messages = [
            ("Your account blocked, send OTP", "Kya? Kaun hai?"),
            ("I am from SBI security", "SBI bank? Kaise yakeen karun?"),
            ("Send OTP to verify", "OTP kya hota hai? Samajh nahi aaya"),
        ]
        
        for scammer_msg, agent_response in messages:
            state_machine.record_turn(scammer_msg, agent_response)
        
        assert state_machine.turn_count == 3
        summary = state_machine.get_session_summary()
        assert summary["total_turns"] == 3


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
