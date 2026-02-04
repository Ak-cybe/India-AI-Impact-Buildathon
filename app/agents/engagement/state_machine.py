"""Conversation State Machine - Manages engagement flow and transitions"""

from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime


class ConversationState(Enum):
    """States in the honeypot conversation flow"""
    INITIAL = "initial"              # First contact from scammer
    CONFUSION = "confusion"          # Persona is confused, asks questions
    BUILDING_TRUST = "building_trust"  # Developing rapport with scammer
    FEIGNED_COMPLIANCE = "feigned_compliance"  # Pretending to comply
    DELAY_TACTICS = "delay_tactics"  # Stalling to extract more intel
    CONCLUSION = "conclusion"        # Wrapping up conversation


class ConversationStateMachine:
    """
    Manages the honeypot engagement lifecycle
    
    Flow:
    INITIAL → CONFUSION → BUILDING_TRUST → FEIGNED_COMPLIANCE → DELAY_TACTICS → CONCLUSION
    
    Key Strategy: Maximize information extraction while maintaining believability
    """
    
    # State transition probabilities based on turn count
    STATE_PROGRESSION = {
        ConversationState.INITIAL: {
            "next_states": [ConversationState.CONFUSION],
            "min_turns": 1,
            "max_turns": 2
        },
        ConversationState.CONFUSION: {
            "next_states": [ConversationState.BUILDING_TRUST, ConversationState.CONFUSION],
            "min_turns": 2,
            "max_turns": 4
        },
        ConversationState.BUILDING_TRUST: {
            "next_states": [ConversationState.FEIGNED_COMPLIANCE],
            "min_turns": 2,
            "max_turns": 5
        },
        ConversationState.FEIGNED_COMPLIANCE: {
            "next_states": [ConversationState.DELAY_TACTICS, ConversationState.FEIGNED_COMPLIANCE],
            "min_turns": 2,
            "max_turns": 6
        },
        ConversationState.DELAY_TACTICS: {
            "next_states": [ConversationState.CONCLUSION, ConversationState.DELAY_TACTICS],
            "min_turns": 2,
            "max_turns": 5
        },
        ConversationState.CONCLUSION: {
            "next_states": [],  # Terminal state
            "min_turns": 1,
            "max_turns": 2
        }
    }
    
    # Response strategies per state
    STATE_STRATEGIES = {
        ConversationState.INITIAL: {
            "goal": "Express surprise and mild concern",
            "tactics": [
                "Ask who is calling",
                "Express confusion about the issue",
                "Ask for clarification"
            ],
            "example_responses": [
                "Kaun bol raha hai? Mujhe samajh nahi aaya...",
                "Kya baat hai? Mera account mein koi problem hai?",
                "Aap kaun hai? Ye konsi company se bol rahe hai?"
            ]
        },
        ConversationState.CONFUSION: {
            "goal": "Extract scammer's claims and build narrative",
            "tactics": [
                "Ask scammer to repeat and explain slowly",
                "Express technical confusion",
                "Ask for official verification"
            ],
            "example_responses": [
                "Mujhe samajh nahi aa raha, thoda dhire boliye na",
                "Ye OTP kya hota hai? Mujhe nahi pata ye sab",
                "Aap sach mein bank se bol rahe ho? Kaise yakeen karun?"
            ]
        },
        ConversationState.BUILDING_TRUST: {
            "goal": "Make scammer believe persona is complying",
            "tactics": [
                "Express willingness to help resolve issue",
                "Share minor (fake) details",
                "Ask for more specific instructions"
            ],
            "example_responses": [
                "Haan haan, main madad karungi, bataiye kya karna hai",
                "Mera phone number hai 98xxxxxxxx, ab kya karun?",
                "Theek hai, main app download karti hoon, phir?"
            ]
        },
        ConversationState.FEIGNED_COMPLIANCE: {
            "goal": "Pretend to follow instructions while extracting info",
            "tactics": [
                "Claim to be doing what scammer asks (but don't)",
                "Report fake errors/issues",
                "Ask for alternative methods (to get more intel)"
            ],
            "example_responses": [
                "Maine link click kiya par error aa raha hai...",
                "OTP aaya hai par galat type ho gaya, dobara bhejo",
                "Ye app install nahi ho raha, koi aur tarika hai?"
            ]
        },
        ConversationState.DELAY_TACTICS: {
            "goal": "Stall and extract maximum intelligence",
            "tactics": [
                "Create fake technical issues",
                "Claim network problems",
                "Say need to get help from family member",
                "Ask scammer for their contact details"
            ],
            "example_responses": [
                "Network bahut slow hai, thodi der mein try karti hoon",
                "Mera beta aayega, usse poochhti hoon ye sab",
                "Aapka WhatsApp number dedo, kal baat karte hain",
                "Ye payment fail ho gaya, aapka UPI ID do"
            ]
        },
        ConversationState.CONCLUSION: {
            "goal": "Gracefully end without alerting scammer",
            "tactics": [
                "Claim battery/phone dying",
                "Say someone came to the door",
                "Claim will call back later"
            ],
            "example_responses": [
                "Battery khatam ho rahi hai, baad mein baat karte hain",
                "Koi aaya hai, main phir call karti hoon",
                "Mujhe doctor ke paas jaana hai, kal baat karein"
            ]
        }
    }
    
    def __init__(self, session_id: str, max_turns: int = 20):
        """
        Initialize state machine for a session
        
        Args:
            session_id: Unique session identifier
            max_turns: Maximum turns before forced conclusion
        """
        self.session_id = session_id
        self.current_state = ConversationState.INITIAL
        self.turn_count = 0
        self.turns_in_current_state = 0
        self.max_turns = max_turns
        self.state_history: List[Dict] = []
        self.created_at = datetime.now()
        self.intelligence_items: List[Dict] = []
    
    def get_current_state(self) -> ConversationState:
        """Get current conversation state"""
        return self.current_state
    
    def get_strategy(self) -> Dict:
        """Get strategy for current state"""
        return self.STATE_STRATEGIES[self.current_state]
    
    def should_transition(self) -> bool:
        """Check if state should transition"""
        progression = self.STATE_PROGRESSION[self.current_state]
        
        # Must stay minimum turns
        if self.turns_in_current_state < progression["min_turns"]:
            return False
        
        # Must transition after max turns
        if self.turns_in_current_state >= progression["max_turns"]:
            return True
        
        # Force conclusion if approaching max total turns
        if self.turn_count >= self.max_turns - 2:
            return True
        
        # Random chance to transition after min turns
        import random
        transition_probability = (
            self.turns_in_current_state - progression["min_turns"]
        ) / (progression["max_turns"] - progression["min_turns"])
        
        return random.random() < transition_probability
    
    def transition(self) -> ConversationState:
        """Transition to next state"""
        progression = self.STATE_PROGRESSION[self.current_state]
        next_states = progression["next_states"]
        
        if not next_states:
            # Already at terminal state
            return self.current_state
        
        # Force conclusion if max turns reached
        if self.turn_count >= self.max_turns:
            self.current_state = ConversationState.CONCLUSION
        else:
            import random
            self.current_state = random.choice(next_states)
        
        # Reset state-specific counter
        self.turns_in_current_state = 0
        
        # Log transition
        self.state_history.append({
            "from_state": self.current_state.value,
            "to_state": self.current_state.value,
            "turn": self.turn_count,
            "timestamp": datetime.now().isoformat()
        })
        
        return self.current_state
    
    def record_turn(self, scammer_message: str, agent_response: str, intelligence_extracted: List[Dict] = None):
        """
        Record a conversation turn
        
        Args:
            scammer_message: What scammer said
            agent_response: What honeypot replied
            intelligence_extracted: Any intel extracted this turn
        """
        self.turn_count += 1
        self.turns_in_current_state += 1
        
        # Store intelligence
        if intelligence_extracted:
            self.intelligence_items.extend(intelligence_extracted)
        
        # Check for state transition
        if self.should_transition():
            self.transition()
    
    def is_session_complete(self) -> bool:
        """Check if session should end"""
        return (
            self.current_state == ConversationState.CONCLUSION and 
            self.turns_in_current_state >= 1
        ) or self.turn_count >= self.max_turns
    
    def get_session_summary(self) -> Dict:
        """Get summary of the session"""
        return {
            "session_id": self.session_id,
            "total_turns": self.turn_count,
            "current_state": self.current_state.value,
            "states_visited": [s["from_state"] for s in self.state_history],
            "intelligence_count": len(self.intelligence_items),
            "created_at": self.created_at.isoformat(),
            "is_complete": self.is_session_complete()
        }
    
    def get_context_for_llm(self) -> str:
        """Generate state context for LLM prompt"""
        strategy = self.get_strategy()
        
        context = f"""
CURRENT CONVERSATION STATE: {self.current_state.value}
Turn: {self.turn_count} / {self.max_turns}

GOAL: {strategy['goal']}

TACTICS TO USE:
{chr(10).join('- ' + t for t in strategy['tactics'])}

EXAMPLE RESPONSES:
{chr(10).join('- ' + r for r in strategy['example_responses'])}

INTELLIGENCE COLLECTED SO FAR: {len(self.intelligence_items)} items
"""
        return context.strip()
