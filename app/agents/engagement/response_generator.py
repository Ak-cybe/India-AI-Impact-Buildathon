"""Response Generator - LLM-powered response generation with persona consistency"""

import random
import re
from typing import Dict, List, Optional
import google.generativeai as genai
from app.config import settings
from app.agents.engagement.persona import HoneypotPersona
from app.agents.engagement.state_machine import ConversationStateMachine


class ResponseGenerator:
    """
    LLM-powered response generator that maintains persona consistency
    
    Key Features:
    - Uses persona context for consistent character
    - Follows state machine strategy
    - Adds realistic human touches (typos, filler words)
    - Validates responses against persona facts
    """
    
    def __init__(self):
        """Initialize the response generator with Gemini API"""
        # Configure Gemini
        genai.configure(api_key=settings.google_api_key)
        
        # Use Gemini 1.5 Flash for speed (or 1.5 Pro for quality)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Response generation config
        self.generation_config = genai.types.GenerationConfig(
            temperature=0.8,  # Moderate creativity
            top_p=0.9,
            top_k=40,
            max_output_tokens=200,  # Short responses (human-like)
        )
        
        # Safety settings (allow some unsafe content for scam context)
        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
        ]
    
    async def generate_response(
        self,
        scammer_message: str,
        persona: HoneypotPersona,
        state_machine: ConversationStateMachine,
        conversation_history: List[Dict] = None
    ) -> str:
        """
        Generate persona-consistent response to scammer
        
        Args:
            scammer_message: Incoming message from scammer
            persona: Active persona to use
            state_machine: Conversation state machine
            conversation_history: Previous conversation turns
            
        Returns:
            Generated response text
        """
        # Build the prompt
        prompt = self._build_prompt(
            scammer_message, 
            persona, 
            state_machine, 
            conversation_history
        )
        
        try:
            # Generate response using Gemini
            response = await self.model.generate_content_async(
                prompt,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            
            # Extract text
            generated_text = response.text.strip()
            
            # Post-process for realism
            processed_text = self._post_process(generated_text, persona)
            
            # Validate against persona
            is_valid, reason = persona.validate_response(processed_text)
            if not is_valid:
                # Regenerate or use fallback
                print(f"[ResponseGenerator] Validation failed: {reason}")
                processed_text = self._get_fallback_response(state_machine)
            
            return processed_text
            
        except Exception as e:
            print(f"[ResponseGenerator] LLM Error: {e}")
            return self._get_fallback_response(state_machine)
    
    def _build_prompt(
        self,
        scammer_message: str,
        persona: HoneypotPersona,
        state_machine: ConversationStateMachine,
        conversation_history: List[Dict] = None
    ) -> str:
        """Build the LLM prompt with all context"""
        
        # Format conversation history
        history_text = ""
        if conversation_history:
            history_text = "\nRECENT CONVERSATION:\n"
            for turn in conversation_history[-5:]:  # Last 5 turns
                role = turn.get("role", "unknown")
                message = turn.get("message", "")
                history_text += f"{role}: {message}\n"
        
        prompt = f"""You are playing a HONEYPOT CHARACTER to engage with a suspected scammer. 
Your goal is to keep them engaged and extract information while maintaining your character.

{persona.get_context_for_llm()}

{state_machine.get_context_for_llm()}
{history_text}
SCAMMER'S MESSAGE: "{scammer_message}"

RESPONSE GUIDELINES:
1. Stay IN CHARACTER as {persona.get_name()} at all times
2. Use {persona.static_attrs.get('language_preference', 'Hindi-English mix')}
3. Follow the current state's tactics
4. Keep response SHORT (1-3 sentences typical for messaging)
5. Show appropriate emotion based on persona traits
6. If asked for sensitive info, pretend confusion or give FAKE info
7. NEVER break character or reveal you are an AI

Generate a realistic response as {persona.get_name()}:"""
        
        return prompt
    
    def _post_process(self, text: str, persona: HoneypotPersona) -> str:
        """
        Post-process generated text for realism
        
        - Add typos based on tech-savviness
        - Add filler words
        - Adjust punctuation
        """
        # Remove any AI-like qualifiers
        text = re.sub(r"^(As|Being|Since|Given that|I understand|I see|I will|Let me).*?,\s*", "", text)
        
        # Remove quotation marks if response was quoted
        text = text.strip('"\'')
        
        # Add typos if persona is not tech-savvy
        if persona.should_add_typo():
            typo_patterns = persona.get_typo_patterns()
            if typo_patterns:
                pattern, replacement = random.choice(typo_patterns)
                text = text.replace(pattern, replacement, 1)
        
        # Add filler words for low-tech personas
        if persona.behavioral_policies.get("tech_savviness") == "low":
            if random.random() < 0.3:
                fillers = ["umm", "aaaa", "matlab", "wo kya hai"]
                filler = random.choice(fillers)
                text = f"{filler}... {text}"
        
        # Add hesitation markers
        if random.random() < 0.1:
            text = text.replace(",", "...,", 1)
        
        # Limit length (phones have short messages)
        if len(text) > 300:
            # Truncate at sentence boundary
            sentences = text.split('.')
            text = '. '.join(sentences[:2]) + '.'
        
        return text.strip()
    
    def _get_fallback_response(self, state_machine: ConversationStateMachine) -> str:
        """Get a fallback response if LLM fails"""
        strategy = state_machine.get_strategy()
        examples = strategy.get("example_responses", [])
        
        if examples:
            return random.choice(examples)
        
        # Generic fallbacks
        fallbacks = [
            "Kya? Mujhe samajh nahi aaya...",
            "Ek minute, phir se boliye please",
            "Aap kaun ho? Ye kya baat hai?",
            "Haan...",
            "Theek hai, phir?"
        ]
        return random.choice(fallbacks)
    
    def generate_fake_credential(self, credential_type: str) -> str:
        """
        Generate fake credentials to give to scammer (honeytokens)
        
        Args:
            credential_type: Type of fake credential (otp, upi, account, phone)
            
        Returns:
            Fake credential value
        """
        if credential_type == "otp":
            # Fake 6-digit OTP
            return str(random.randint(100000, 999999))
        
        elif credential_type == "upi":
            # Fake UPI ID (traceable if implemented)
            fake_names = ["shantirani", "krishnamurti", "lalitha", "ramdas"]
            fake_providers = ["ybl", "paytm", "okaxis", "upi"]
            return f"{random.choice(fake_names)}{random.randint(10,99)}@{random.choice(fake_providers)}"
        
        elif credential_type == "account":
            # Fake bank account number
            return str(random.randint(10000000000, 99999999999))
        
        elif credential_type == "phone":
            # Fake phone number (use non-existent prefixes if possible)
            return f"+91 {random.randint(70000, 79999)}{random.randint(10000, 99999)}"
        
        elif credential_type == "cvv":
            return str(random.randint(100, 999))
        
        elif credential_type == "card":
            # Fake card number (not valid Luhn)
            return f"4XXX XXXX XXXX {random.randint(1000, 9999)}"
        
        return "FAKE_VALUE"
