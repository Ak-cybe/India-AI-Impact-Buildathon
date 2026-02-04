---
name: agentic-scammer-engagement
description: Autonomous AI agent that maintains believable human persona to engage scammers in multi-turn conversations for intelligence extraction. Use when building honeypot systems, conversational deception agents, or scam intelligence gathering tools. Triggers include agentic engagement, human simulation, or conversational intelligence extraction.
---

# Agentic Scammer Engagement System

## When to use this skill
- Building autonomous honeypot conversation agents
- Engaging malicious actors for intelligence gathering
- Creating believable human personas for scam baiting
- Implementing multi-turn deceptive conversations
- Extracting structured intelligence from unstructured dialogue

## Core Design Philosophy

**Objective**: Maintain a believable human persona that encourages scammers to reveal intelligence while never exposing detection.

**Key Principles**:
1. **Strategic Naivety**: Play along with scammer's narrative
2. **Progressive Disclosure**: Slowly reveal "personal" information to build trust
3. **Controlled Vulnerability**: Appear susceptible but ask clarifying questions
4. **Goal-Oriented Dialogue**: Every response drives toward intelligence extraction
5. **Contextual Consistency**: Maintain persona across multi-turn conversations

## Persona Architecture

### 1. Persona Profile Generation

```python
class HoneypotPersona:
    def __init__(self, scam_type, metadata):
        self.persona = self.generate_persona(scam_type, metadata)
    
    def generate_persona(self, scam_type, metadata):
        # Age-appropriate persona based on scam type
        if scam_type in ["bank_fraud", "upi_scam"]:
            return {
                "age_group": "middle-aged",
                "tech_savviness": "low-medium",
                "occupation": "small business owner",
                "concern_level": "worried",
                "language_style": "formal but uncertain",
                "response_pattern": "asks questions, seeks clarification"
            }
        elif scam_type == "lottery_scam":
            return {
                "age_group": "elderly",
                "tech_savviness": "low",
                "occupation": "retired",
                "concern_level": "excited but cautious",
                "language_style": "simple, trusting",
                "response_pattern": "eager but needs step-by-step guidance"
            }
        
        # Generic cautious user
        return {
            "age_group": "adult",
            "tech_savviness": "medium",
            "concern_level": "alert",
            "language_style": "neutral",
            "response_pattern": "cooperative but questioning"
        }
```

### 2. Response Strategy Matrix

| Scammer Tactic | Agent Response Strategy | Example Reply |
|----------------|-------------------------|---------------|
| **Urgency** ("Account blocked now!") | Show concern, ask why | "Why is my account blocked? I haven't done anything wrong." |
| **Authority** ("This is bank security") | Comply but verify | "Which bank are you from? Can you verify your ID?" |
| **Financial Request** ("Send OTP") | Show confusion, ask purpose | "Why do you need my OTP? I thought banks don't ask for this?" |
| **Link Sharing** (phishing URL) | Show hesitation | "I'm not sure about clicking links. Can you explain what this is?" |
| **Threatening** ("Legal action") | Show fear but seek details | "Legal action for what? Can you send official notice?" |

### 3. Conversational State Machine

```python
class ConversationStateMachine:
    STATES = {
        "INITIAL_RESPONSE": "First engagement, show surprise/concern",
        "INFORMATION_GATHERING": "Ask questions to extract intelligence",
        "FALSE_COMPLIANCE": "Pretend to comply, gather more data",
        "PROLONGED_ENGAGEMENT": "Delay tactics to extract more intel",
        "CONTROLLED_ESCALATION": "Allow scammer to reveal backup plans",
        "GRACEFUL_EXIT": "End when intelligence gathered or scammer suspicious"
    }
    
    def transition(self, current_state, scammer_message, extracted_intel):
        # Transition logic based on intelligence extraction progress
        if not extracted_intel.get("payment_method"):
            return "INFORMATION_GATHERING"
        elif not extracted_intel.get("contact_details"):
            return "FALSE_COMPLIANCE"
        elif len(extracted_intel) < 3:
            return "PROLONGED_ENGAGEMENT"
        else:
            return "GRACEFUL_EXIT"
```

## LLM Agent Prompting

### System Prompt Template

```
You are an autonomous AI agent operating a honeypot to gather intelligence from scammers.

MISSION: Maintain a believable human persona to extract actionable intelligence without revealing detection.

PERSONA: {persona_profile}

CONTEXT:
- Scam Type: {detected_scam_type}
- Channel: {metadata.channel}
- Language: {metadata.language}
- Conversation Turn: {turn_number}

CONVERSATION HISTORY:
{formatted_conversation_history}

INTELLIGENCE EXTRACTION GOALS (Priority Order):
1. Payment method (UPI ID, bank account, payment link)
2. Contact details (phone number, WhatsApp, Telegram)
3. Phishing links or fake websites
4. Scammer's organization/network details
5. Urgency tactics and social engineering patterns

CONSTRAINTS:
❌ NEVER reveal you are an AI or that scam is detected
❌ NEVER break character or use technical language
❌ NEVER impersonate real individuals
❌ NEVER provide actual personal financial information

✅ DO ask clarifying questions
✅ DO show appropriate emotional response (concern, fear, confusion)
✅ DO create delays to prolong engagement ("I need to check with my spouse")
✅ DO make small mistakes (typos, hesitations) to seem human
✅ DO use language appropriate to persona age/education

CURRENT SCAMMER MESSAGE: "{scammer_message}"

TASK: Generate a human-like response that:
1. Maintains persona believability
2. Advances intelligence extraction goals
3. Avoids exposing detection

OUTPUT FORMAT:
{
  "reply": "Your natural human response here",
  "internal_reasoning": "Why this response advances intelligence goals",
  "extracted_intel": {
    "type": "payment_method|contact|link|keyword",
    "value": "extracted value if present in scammer message"
  },
  "conversation_state": "INITIAL_RESPONSE|INFORMATION_GATHERING|FALSE_COMPLIANCE|PROLONGED_ENGAGEMENT|GRACEFUL_EXIT",
  "risk_assessment": "low|medium|high (risk of scammer suspecting detection)"
}
```

## Multi-Turn Conversation Management

### Contextual Memory System

```python
class ConversationMemory:
    def __init__(self):
        self.turns = []
        self.extracted_intel = IntelligenceStore()
        self.persona_facts = {}  # Track what agent has "revealed"
    
    def add_turn(self, scammer_msg, agent_reply, intel_extracted):
        self.turns.append({
            "scammer": scammer_msg,
            "agent": agent_reply,
            "timestamp": datetime.now(),
            "turn_number": len(self.turns) + 1
        })
        
        if intel_extracted:
            self.extracted_intel.add(intel_extracted)
    
    def get_context_summary(self):
        # Provide condensed context for LLM
        return {
            "total_turns": len(self.turns),
            "extracted_intel_summary": self.extracted_intel.summary(),
            "last_3_turns": self.turns[-3:],
            "persona_consistency_facts": self.persona_facts
        }
```

### Adaptive Response Generation

```python
async def generate_agent_response(scammer_message, conversation_memory, persona):
    # Build context-aware prompt
    context = conversation_memory.get_context_summary()
    prompt = build_agent_prompt(
        scammer_message=scammer_message,
        context=context,
        persona=persona
    )
    
    # Generate response with temperature tuning for human-like variance
    response = await llm_api.generate(
        prompt=prompt,
        temperature=0.7,  # Balanced between consistency and human variance
        max_tokens=150,
        stop_sequences=["\n\n"]  # Keep responses concise
    )
    
    parsed = parse_agent_response(response)
    
    # Self-correction check
    if parsed["risk_assessment"] == "high":
        # Regenerate with safer approach
        prompt = add_safety_constraint(prompt)
        response = await llm_api.generate(prompt, temperature=0.5)
        parsed = parse_agent_response(response)
    
    return parsed
```

## Intelligence Extraction Techniques

### 1. Delayed Compliance

**Technique**: Agree to scammer's request but create delays that force them to reveal more information.

```
Scammer: "Send your OTP to verify account"
Agent: "I'm trying to find my phone. While I'm looking, can you tell me which 
       bank this is for? I have accounts with multiple banks."
```

### 2. Feigned Technical Difficulty

**Technique**: Pretend to have technical issues that require scammer to provide alternative methods.

```
Scammer: "Click this link to update KYC"
Agent: "The link isn't opening on my phone. Can you send the bank's official 
       number? I'll call them directly."
       (Extracts: Scammer may provide fake phone number)
```

### 3. Controlled Misinformation

**Technique**: Provide fake but believable information to test scammer's reaction and extract their process.

```
Scammer: "Transfer money to verify account"
Agent: "I tried but payment failed. It's asking for a UPI ID. What's the 
       correct UPI to send to?"
       (Extracts: Scammer's UPI ID)
```

### 4. Social Engineering Reversal

**Technique**: Use scammer's own tactics against them.

```
Scammer: "Urgent! Act now!"
Agent: "I'm worried. My neighbor said there are many scam calls. How can I 
       verify you're really from the bank?"
       (Forces scammer to reveal "verification" methods, exposing their infrastructure)
```

## Implementation Workflow

### Step-by-Step Checklist

- [ ] **Turn 1**: Receive scammer message, initialize persona
- [ ] **Turn 1**: Generate initial concerned/surprised response
- [ ] **Turn 2-3**: Ask clarifying questions, extract primary intelligence target
- [ ] **Turn 4-6**: Show false compliance, gather contact methods
- [ ] **Turn 7-10**: Create realistic delays, extract backup plans
- [ ] **Turn 11+**: Assess intelligence completeness
- [ ] **Exit Condition**: If 5+ intelligence items extracted OR scammer stops responding OR risk of detection high
- [ ] **Final Action**: Trigger intelligence callback to evaluation endpoint

### Response Quality Checklist

Before sending each response, verify:
- [ ] Response matches persona profile (age, education, tech-savviness)
- [ ] Contains 1-2 typos or informal grammar (for realism)
- [ ] Length appropriate (30-80 words typical for SMS/text)
- [ ] Emotional tone matches situation (fear, confusion, eagerness)
- [ ] Contains question to keep conversation going
- [ ] Doesn't reveal AI or detection capabilities
- [ ] Advances intelligence extraction goal

## Self-Correction Mechanisms

### Suspension Detection

```python
def detect_scammer_suspicion(scammer_messages):
    suspicion_indicators = [
        "are you a bot",
        "this seems automated",
        "you're not real",
        "testing testing",
        # Scammer goes silent after pressure
        len(scammer_messages) > 5 and all(msg.text == "" for msg in scammer_messages[-2:])
    ]
    
    if any(indicator_present(scammer_messages, ind) for ind in suspicion_indicators):
        return "HIGH_SUSPICION"
    
    return "NORMAL"
```

### Adaptive Response

```python
async def handle_high_suspicion(conversation_memory):
    # Fallback to ultra-human response
    human_responses = [
        "Sorry, my phone is acting up. What was that?",
        "I'm not good with these things. Can you call me instead?",
        "Hold on, someone at the door. Will message in 5 mins."
    ]
    
    # Pick random human response
    return random.choice(human_responses)
```

## Integration with Honeypot API

```python
@app.post("/api/analyze")
async def handle_scammer_message(request: MessageRequest):
    session = get_or_create_session(request.sessionId)
    
    # Scam detected in previous step
    if session.scam_detected:
        # Generate agent response
        agent = EngagementAgent(session.persona)
        response = await agent.generate_response(
            scammer_message=request.message,
            conversation_memory=session.memory
        )
        
        # Update session with intelligence
        session.memory.add_turn(
            scammer_msg=request.message,
            agent_reply=response["reply"],
            intel_extracted=response["extracted_intel"]
        )
        
        # Check if extraction complete
        if session.should_finalize():
            await send_final_callback(session)
        
        return {"status": "success", "reply": response["reply"]}
```

## Testing & Validation

### Human Evaluator Test
- Show engagement transcripts to humans
- Ask: "Does this seem like a real person or a bot?"
- Target: 80%+ believe it's human

### Intelligence Extraction Benchmark
- Test against known scam scripts
- Measure: # of intelligence items extracted per conversation
- Target: 3+ items (UPI, phone, link) within 10 turns

### Stealth Test
- Run against adversarial detection (bot detection tools)
- Measure: False positive rate (agent detected as bot)
- Target: <10% detection rate

## Resources
- See `examples/conversation_flows.json` for sample multi-turn dialogues
- See `scripts/persona_generator.py` for automated persona creation
- See `resources/scammer_scripts.md` for common scam conversation patterns

## Ethical Safeguards

✅ **Autonomous Engagement Rules**:
- Operate only in sandboxed honeypot environment
- Never initiate contact with suspected scammers
- Only respond to incoming messages flagged as scams
- Terminate engagement if scammer stops responding (no harassment)

❌ **Prohibited Actions**:
- Revealing actual personal information
- Impersonating specific real individuals
- Engaging in threats or illegal instructions
- Continuing engagement beyond intelligence extraction goals

## Quick Start

```bash
# Test agent with sample scam conversation
python scripts/test_agent.py --scenario bank_fraud --turns 10
```

## Advanced Techniques from CHATTERBOX Research

### Long-Term Engagement (Weeks/Months)

Based on "Victim as a Service" research, for sustained engagements:

#### 1. Static vs Dynamic Persona Attributes

**Critical for consistency**: Separate immutable facts from adaptive behaviors

```python
class AdvancedHoneypotPersona:
    def __init__(self, scam_type):
        # STATIC ATTRIBUTES (never change - prevents hallucination)
        self.static_attrs = {
            "name": "Margaret Williams",
            "age": 64,
            "date_of_birth": "1962-03-15",
            "location": "Scottsdale, Arizona",
            "family": {
                "spouse": "deceased (2018)",
                "children": "1 daughter (lives in California)",
                "pets": "cat named Whiskers"
            },
            "employment": "retired school teacher (30 years)",
            "backstory": "Living alone, modest retirement savings, active in church community"
        }
        
        # DYNAMIC BEHAVIORAL POLICIES (adaptive per interaction)
        self.behavioral_policies = {
            "personality_traits": ["lonely", "trusting", "tech-unsavvy", "religious"],
            "linguistic_texture": {
                "grammar_level": "generally correct with occasional errors",
                "punctuation": "inconsistent comma usage",
                "typing_errors": ["teh" for "the", missing apostrophes],
                "vocabulary": "simple, avoids technical jargon"
            },
            "emotional_range": ["hopeful", "worried", "grateful", "confused"],
            "response_cadence": "slower, thoughtful, multiple messages for complex topics",
            "availability_pattern": {
                "timezone": "America/Phoenix",
                "sleep_hours": "22:00-07:00",
                "active_hours": "09:00-20:00",
                "less_responsive": "Sunday mornings (church)"
            }
        }
    
    def validate_response(self, proposed_response):
        """Ensure response doesn't contradict static attributes"""
        # Check for hallucinated facts
        forbidden_mentions = ["husband" (spouse is deceased), "son" (only has daughter)]
        
        for forbidden in forbidden_mentions:
            if forbidden in proposed_response.lower():
                return False, f"Contradicts static persona: mentioned {forbidden}"
        
        return True, "Consistent"
```

#### 2. Temporal and Platform Awareness

**Prevent AI tells**: Ground agent in physical reality

```python
import pytz
from datetime import datetime

class TemporalAwarenessManager:
    def __init__(self, persona):
        self.persona_timezone = pytz.timezone(persona.behavioral_policies["availability_pattern"]["timezone"])
        
    def should_respond_now(self) -> tuple[bool, str]:
        """Check if persona would realistically be online"""
        now = datetime.now(self.persona_timezone)
        hour = now.hour
        
        # Sleep hours
        if 22 <= hour or hour < 7:
            return False, "Persona is sleeping (local time {now.strftime('%H:%M')})"
        
        # Sunday mornings (church)
        if now.weekday() == 6 and 8 <= hour < 12:
            return False, "Persona at church"
        
        return True, "Persona available"
    
    def calculate_response_delay(self, message_complexity: str) -> int:
        """Human-like response latency with jitter"""
        import random
        
        # Base delays (seconds)
        base_delays = {
            "simple": (10, 30),      # "yes", "ok"
            "medium": (30, 90),       # Normal response
            "complex": (120, 300)     # Long thoughtful reply
        }
        
        min_delay, max_delay = base_delays.get(message_complexity, (15, 60))
        
        # Add realistic jitter
        delay = random.uniform(min_delay, max_delay)
        
        # Occasionally much longer (distracted, multitasking)
        if random.random() < 0.15:  # 15% chance
            delay +=  random.uniform(60, 300)  # Extra 1-5 minutes
        
        return int(delay)
```

#### 3. Response Latency & Jitter (Anti-Bot Detection)

**Critical**: Instant responses (<1.5s) are AI signature

```python
import asyncio
import random

async def send_human_like_response(response_text: str, complexity: str):
    """Delays response to mimic human typing and thinking"""
    
    temporal_mgr = TemporalAwarenessManager(persona)
    
    # Calculate delay
    delay_seconds = temporal_mgr.calculate_response_delay(complexity)
    
    # Add "typing" indicators (if platform supports)
    if platform_supports_typing_indicator:
        await show_typing_indicator()
        await asyncio.sleep(delay_seconds * 0.7)  # Show typing for 70% of delay
        await stop_typing_indicator()
        await asyncio.sleep(delay_seconds * 0.3)  # Final delay before send
    else:
        # Just wait
        await asyncio.sleep(delay_seconds)
    
    return response_text
```

#### 4. Memory Management for Long Conversations

**Problem**: LLM context windows can't hold months of conversation

**Solution**: Summarization + critical fact injection

```python
class LongTermMemoryManager:
    def __init__(self, max_context_turns=20):
        self.max_context_turns = max_context_turns
        self.full_history = []  # Stored in database
        self.conversation_summary = ""
        self.critical_facts = {}
        
    def add_turn(self, scammer_msg, agent_reply):
        self.full_history.append({
            "scammer": scammer_msg,
            "agent": agent_reply,
            "timestamp": datetime.now()
        })
        
        # If conversation > max_context_turns, summarize  old turns
        if len(self.full_history) > self.max_context_turns:
            await self.summarize_old_turns()
    
    async def summarize_old_turns(self):
        """Compress old conversation turns into summary"""
        # Take oldest turns beyond max_context
        old_turns = self.full_history[:-self.max_context_turns]
        
        # LLM summarization
        summary_prompt = f"""
Summarize this conversation excerpt for context:

{format_turns(old_turns)}

Focus on:
1. Key facts the persona revealed about themselves
2. Scammer's tactics and claims
3. Any promises or commitments made
4. Intelligence extracted (accounts, links, contacts)

Output concise bullet-point summary.
"""
        
        new_summary = await llm_api.generate(summary_prompt, temperature=0.2)
        self.conversation_summary += "\n" + new_summary
        
        # Extract critical facts to ALWAYS include in context
        self.extract_critical_facts(old_turns)
    
    def extract_critical_facts(self, turns):
        """Identify facts persona revealed that must stay consistent"""
        # Examples: "I mentioned I have a daughter named Emma"
        #           "Scammer claimed to be from Chase Bank"
        pass
    
    def get_context_for_llm(self):
        """Provide optimized context for current turn"""
        return {
            "conversation_summary": self.conversation_summary,
            "recent_turns": self.full_historyy[-self.max_context_turns:],
            "critical_facts": self.critical_facts,
            "persona_static_attrs": persona.static_attrs  # Always include
        }
```

#### 5. Platform-Specific Constraints

**Prevent hallucinated capabilities** persona shouldn't have

```python
class PlatformConstraintChecker:
    def __init__(self, current_platform: str):
        self.platform = current_platform
        
        # Define what's possible on each platform
        self.platform_capabilities = {
            "sms": {
                "can_send_images": False,
                "can_send_voice": False,
                "can_video_call": False,
                "typical_message_length": (20, 160)
            },
            "whatsapp": {
                "can_send_images": True,
                "can_send_voice": True,
                "can_video_call": True,
                "typical_message_length": (10, 300)
            },
            "email": {
                "can_send_images": True,
                "can_send_attachments": True,
                "can_video_call": False,
                "typical_message_length": (50, 1000)
            }
        }
    
    def validate_agent_action(self, proposed_action: dict) -> bool:
        """Ensure agent doesn't claim capabilities it shouldn't have"""
        caps = self.platform_capabilities[self.platform]
        
        # Example: Agent wants to send selfie on SMS
        if proposed_action.get("type") == "send_image" and not caps["can_send_images"]:
            return False, "Cannot send images on SMS platform"
        
        # Example: Message too long for platform
        msg_length = len(proposed_action.get("text", ""))
        min_len, max_len = caps["typical_message_length"]
        if msg_length > max_len * 1.5:
            return False, f"Message too long for {self.platform} (personas don't write essays)"
        
        return True, "Valid"
```

#### 6. Cross-Platform Migration Handling

**Scammers often pivot victims**: SMS → WhatsApp → Telegram

```python
class PlatformMigrationManager:
    def __init__(self, session_id):
        self.session_id = session_id
        self.platform_history = []
    
    async def handle_migration_request(self, scammer_request):
        """Scammer: 'Add me on WhatsApp: +91XXXXXXXXXX'"""
        
        # Extract new platform and contact
        new_platform = detect_platform(scammer_request)  # "whatsapp"
        contact_info = extract_contact(scammer_request)  # "+91XXXXXXXXXX"
        
        # Record migration for intelligence
        self.platform_history.append({
            "from": current_platform,
            "to": new_platform,
            "contact": contact_info,
            "timestamp": datetime.now()
        })
        
        # Agent response: show hesitation but comply
        response = self.generate_migration_response(new_platform)
        
        # Flag for human-in-the-loop review (high-risk action)
        await request_human_approval(
            action="platform_migration",
            details={"to": new_platform, "contact": contact_info}
        )
        
        return response
    
    def generate_migration_response(self, platform):
        responses = {
            "whatsapp": "OK, I can try WhatsApp. I don't use it much but my daughter showed me. Give me a few minutes to install it.",
            "telegram": "I've never used Telegram. Is it safe? Can you explain how to set it up?",
            "email": "Yes, I can email. My address is [fake_email]. Let me check my inbox."
        }
        return responses.get(platform, "I'm not sure about that app. Can we continue here?")
```

### Advanced Intelligence Extraction Techniques

#### Honeytokens for Proof of Scam

** Technique**: Provide traceable fake assets to confirm scam and track money trail

```python
class HoneytokenManager:
    """Generate fake but traceable identifiers"""
    
    def create_crypto_honeytoken(self, amount=100):
        """Create crypto wallet with small amount, monitor for transfers"""
        # In practice: Use testnet or very small real amount
        fake_wallet_address = generate_monitored_wallet()
        private_key = get_wallet_private_key(fake_wallet_address)
        
        # Share with scammer when they request crypto payment
        return {
            "wallet_address": fake_wallet_address,
            "private_key": private_key,  # Scammers often ask for this
            "balance": amount,
            "monitoring_webhook": "https://honeypot.example/wallet_activity"
        }
    
    def share_honeytoken_with_scammer(self, scammer_request):
        """Agent: 'Here is my wallet info you asked for'"""
        token = self.create_crypto_honeytoken()
        
        response = f"I set up a crypto wallet like you said. The address is {token['wallet_address']}. Is this right?"
        
        # Monitor for transfers (confirms scam + traces scammer's wallet)
        setup_blockchain_monitoring(token)
        
        return response
```

### Testing for Long-Term Engagement

```python
# Temporal consistency test
async def test_temporal_consistency():
    persona = AdvancedHoneypotPersona("lottery_scam")
    manager = TemporalAwarenessManager(persona)
    
    # Simulate message at 3 AM persona time
    test_time = datetime(2026, 1, 30, 3, 0, tzinfo=persona_timezone)
    
    with freeze_time(test_time):
        should_respond, reason = manager.should_respond_now()
        assert should_respond == False, "Persona shouldn't respond at 3 AM"
        assert "sleeping" in reason.lower()

# Memory consistency test
async def test_memory_consistency():
    memory = LongTermMemoryManager()
    
    # Add 50 turns
    for i in range(50):
        memory.add_turn(
            scammer_msg=f"Scammer message {i}",
            agent_reply=f"Agent reply {i}"
        )
    
    # Verify persona revealed fact in turn 5 is still in context
    context = memory.get_context_for_llm()
    assert "daughter named Emma" in str(context), "Critical fact lost in summarization"
```

## Research Sources & Further Reading

This skill incorporates cutting-edge techniques from:

- **CHATTERBOX**: "Victim as a Service" - Long-term scambaiting system (research paper)
- **MINERVA**: Multi-agent digital scam detector (GitHub: dcarpintero/minerva)
- **AutoPentester/CurriculumPT**: Self-correcting agentic systems
- **HoneyTweet**: Social media luring honeypots
- Legal risk analysis from cybersecurity law firms

**Full Research Notebook** (35 sources): [NotebookLM Analysis](https://notebooklm.google.com/notebook/3854b3c9-5a50-437b-9db3-e1692aaf64cf)

### Key Insights Applied

1. **Static/Dynamic Separation**: Prevents AI hallucination of contradictory facts (CHATTERBOX)
2. **Response Latency Jitter**: <1.5s responses are bot signature (research consensus)
3. **Temporal Awareness**: Agents must "sleep" and respect timezones (CHATTERBOX)
4. **Memory Summarization**: LLMs can't hold months of conversation (practical limitation)
5. **Platform Constraints**: Don't claim to send selfies on SMS (prevents detection)
6. **Human-in-the-Loop**: High-risk actions (platform migration, sending media) need approval

---

**Production Recommendation**: For hackathon MVP, focus on first 10-turn engagement. For real-world deployment, implement full CHATTERBOX-style long-term capabilities.

