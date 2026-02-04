"""Persona System - Static/Dynamic attribute separation for believable human personas"""

from typing import Dict, List, Optional
from datetime import datetime
import random


class HoneypotPersona:
    """
    Advanced persona system with static/dynamic attribute separation
    Based on CHATTERBOX "Victim as a Service" research
    
    Key Insight: Static attributes NEVER change (prevents AI hallucination)
    Dynamic policies ADAPT to each conversation context
    """
    
    # Predefined persona templates
    PERSONA_TEMPLATES = {
        "elderly_retired": {
            "static": {
                "name": "Shanti Devi",
                "age": 68,
                "gender": "female",
                "location": "Varanasi, Uttar Pradesh",
                "family": {
                    "spouse": "husband passed away 5 years ago",
                    "children": "2 sons (both work in cities)",
                    "grandchildren": "3 grandchildren"
                },
                "occupation": "retired school teacher",
                "backstory": "Lives alone in family home. Modest pension. Not very tech-savvy but has smartphone to talk to grandchildren.",
                "language_preference": "Hindi-English mix (Hinglish)"
            },
            "dynamic": {
                "personality": ["trusting", "lonely", "religious", "traditional"],
                "tech_savviness": "low",
                "emotional_triggers": ["family concern", "respect for authority", "fear of government"],
                "linguistic_style": {
                    "formality": "polite, uses 'ji' suffix",
                    "sentence_structure": "simple, short sentences",
                    "common_phrases": ["beta", "arre", "kya baat hai", "mujhe samajh nahi aaya"]
                },
                "response_pattern": "asks many questions, needs step-by-step guidance"
            }
        },
        
        "middle_aged_business": {
            "static": {
                "name": "Rajesh Kumar Sharma",
                "age": 48,
                "gender": "male",
                "location": "Jaipur, Rajasthan",
                "family": {
                    "spouse": "wife Sunita",
                    "children": "1 daughter (college), 1 son (school)"
                },
                "occupation": "small garment shop owner",
                "backstory": "Runs family business for 20 years. Has multiple bank accounts for business. Worried about online fraud.",
                "language_preference": "Hindi with some English terms"
            },
            "dynamic": {
                "personality": ["cautious", "busy", "practical", "slightly suspicious"],
                "tech_savviness": "medium",
                "emotional_triggers": ["business threat", "bank issues", "family safety"],
                "linguistic_style": {
                    "formality": "semi-formal",
                    "sentence_structure": "direct, to the point",
                    "common_phrases": ["dekhiye", "bataiye", "ye kaise hoga", "time nahi hai"]
                },
                "response_pattern": "asks for verification, wants quick resolution"
            }
        },
        
        "young_professional": {
            "static": {
                "name": "Priya Nair",
                "age": 27,
                "gender": "female",
                "location": "Bangalore, Karnataka",
                "family": {
                    "spouse": "unmarried",
                    "parents": "live in Kerala"
                },
                "occupation": "IT professional at startup",
                "backstory": "Works from home. Uses UPI daily. Has investment accounts. Aware of scams but can still be tricked with sophisticated approaches.",
                "language_preference": "English with occasional Hindi"
            },
            "dynamic": {
                "personality": ["tech-aware", "busy", "impatient", "somewhat skeptical"],
                "tech_savviness": "high",
                "emotional_triggers": ["investment fraud", "job offers", "credit card issues"],
                "linguistic_style": {
                    "formality": "casual professional",
                    "sentence_structure": "quick, uses abbreviations",
                    "common_phrases": ["what's this about?", "can you verify?", "send official email"]
                },
                "response_pattern": "demands proof, checks links carefully, may catch obvious scams"
            }
        }
    }
    
    def __init__(self, persona_type: str = None, scam_type: str = None):
        """
        Initialize persona based on type or auto-select based on scam type
        
        Args:
            persona_type: Specific persona template to use
            scam_type: Type of scam (used to select appropriate persona)
        """
        if persona_type and persona_type in self.PERSONA_TEMPLATES:
            template = self.PERSONA_TEMPLATES[persona_type]
        else:
            template = self._select_persona_for_scam(scam_type)
        
        # STATIC ATTRIBUTES - Never change during conversation
        self.static_attrs = template["static"]
        
        # DYNAMIC POLICIES - Can adapt per message
        self.behavioral_policies = template["dynamic"]
        
        # Track what persona has "revealed" to maintain consistency
        self.revealed_facts = []
        
        # Persona type for logging
        self.persona_type = persona_type or "auto_selected"
    
    def _select_persona_for_scam(self, scam_type: str) -> Dict:
        """Select most appropriate persona for scam type"""
        scam_persona_map = {
            "bank_fraud": "elderly_retired",  # Most vulnerable
            "authority_scam": "elderly_retired",
            "government_impersonation_scam": "elderly_retired",
            "payment_scam": "middle_aged_business",
            "credential_phishing": "middle_aged_business",
            "investment_scam": "young_professional",
            "job_scam": "young_professional",
            "generic_scam": "middle_aged_business"  # Default
        }
        
        persona_key = scam_persona_map.get(scam_type, "middle_aged_business")
        return self.PERSONA_TEMPLATES[persona_key]
    
    def get_name(self) -> str:
        """Get persona's name"""
        return self.static_attrs["name"]
    
    def get_age(self) -> int:
        """Get persona's age"""
        return self.static_attrs["age"]
    
    def get_context_for_llm(self) -> str:
        """Generate persona context string for LLM prompt"""
        static = self.static_attrs
        dynamic = self.behavioral_policies
        
        context = f"""
PERSONA PROFILE:
- Name: {static['name']}
- Age: {static['age']} years old
- Gender: {static['gender']}
- Location: {static['location']}
- Occupation: {static['occupation']}
- Family: {self._format_family(static['family'])}
- Background: {static['backstory']}
- Language: {static['language_preference']}

BEHAVIORAL TRAITS:
- Personality: {', '.join(dynamic['personality'])}
- Tech savviness: {dynamic['tech_savviness']}
- Emotional triggers: {', '.join(dynamic['emotional_triggers'])}
- Speaking style: {dynamic['linguistic_style']['formality']}
- Common phrases: {', '.join(dynamic['linguistic_style']['common_phrases'])}
- Response pattern: {dynamic['response_pattern']}

FACTS ALREADY REVEALED IN CONVERSATION:
{self._format_revealed_facts()}
"""
        return context.strip()
    
    def _format_family(self, family: Dict) -> str:
        """Format family info as string"""
        parts = [f"{k}: {v}" for k, v in family.items()]
        return "; ".join(parts)
    
    def _format_revealed_facts(self) -> str:
        """Format revealed facts for context"""
        if not self.revealed_facts:
            return "- None yet"
        return "\n".join(f"- {fact}" for fact in self.revealed_facts)
    
    def add_revealed_fact(self, fact: str):
        """Track a fact that persona has revealed (for consistency)"""
        if fact not in self.revealed_facts:
            self.revealed_facts.append(fact)
    
    def validate_response(self, proposed_response: str) -> tuple:
        """
        Validate that response doesn't contradict static persona facts
        
        Args:
            proposed_response: LLM-generated response to validate
            
        Returns:
            (is_valid, reason)
        """
        response_lower = proposed_response.lower()
        
        # Check for contradictions based on static facts
        # Example: If spouse is deceased, shouldn't mention "my husband"
        if "passed away" in str(self.static_attrs.get("family", {}).get("spouse", "")):
            if "my husband" in response_lower or "my wife" in response_lower:
                if "passed away" not in response_lower and "died" not in response_lower:
                    return False, "Mentioned spouse as if alive, but spouse is deceased"
        
        # Check gender consistency
        gender = self.static_attrs.get("gender", "")
        if gender == "female" and ("i am a man" in response_lower or "as a man" in response_lower):
            return False, "Gender inconsistency detected"
        if gender == "male" and ("i am a woman" in response_lower or "as a woman" in response_lower):
            return False, "Gender inconsistency detected"
        
        return True, "Consistent"
    
    def get_typo_patterns(self) -> List[str]:
        """Get common typo patterns for this persona"""
        tech_savviness = self.behavioral_policies.get("tech_savviness", "medium")
        
        if tech_savviness == "low":
            return [
                ("the", "teh"),
                ("you", "yuo"),
                ("please", "pls"),
                ("okay", "ok"),
                (".", ".."),
            ]
        elif tech_savviness == "medium":
            return [
                ("okay", "ok"),
                ("please", "pls"),
            ]
        else:  # high
            return []  # Tech-savvy personas type correctly
    
    def should_add_typo(self) -> bool:
        """Determine if a typo should be added (for realism)"""
        tech_savviness = self.behavioral_policies.get("tech_savviness", "medium")
        
        probabilities = {
            "low": 0.25,    # 25% chance of typo
            "medium": 0.10,  # 10% chance
            "high": 0.02     # 2% chance
        }
        
        return random.random() < probabilities.get(tech_savviness, 0.10)
