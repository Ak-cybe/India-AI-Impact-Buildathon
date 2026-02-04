---
name: intelligence-extraction-callback
description: Extracts structured intelligence from scammer conversations and sends mandatory final result callback to evaluation endpoints. Use when completing honeypot engagements, finalizing intelligence reports, or submitting scam analysis results. Triggers include intelligence extraction, final callback, or evaluation submission.
---

# Intelligence Extraction & Final Callback System

## When to use this skill
- Completing honeypot conversation cycles
- Extracting structured intelligence from unstructured scammer dialogues
- Sending mandatory evaluation callbacks
- Generating scam behavior analysis reports
- Finalizing intelligence gathering missions

## Intelligence Extraction Architecture

### 1. Intelligence Data Model

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class ExtractedIntelligence(BaseModel):
    # Financial Intelligence
    bankAccounts: List[str] = Field(default_factory=list, description="Bank account numbers")
    upiIds: List[str] = Field(default_factory=list, description="UPI payment IDs")
    paymentLinks: List[str] = Field(default_factory=list, description="Payment gateway links")
    
    # Digital Infrastructure
    phishingLinks: List[str] = Field(default_factory=list, description="Malicious URLs")
    phoneNumbers: List[str] = Field(default_factory=list, description="Contact numbers")
    emailAddresses: List[str] = Field(default_factory=list, description="Email contacts")
    socialMedia: List[str] = Field(default_factory=list, description="WhatsApp, Telegram, etc.")
    
    # Behavioral Intelligence
    suspiciousKeywords: List[str] = Field(default_factory=list, description="Scam tactics keywords")
    urgencyTactics: List[str] = Field(default_factory=list, description="Urgency phrases used")
    impersonationClaims: List[str] = Field(default_factory=list, description="Authority claims")
    
    # Metadata
    scamType: Optional[str] = Field(None, description="bank_fraud|upi_scam|phishing|lottery|impersonation")
    attackVector: Optional[str] = Field(None, description="SMS|WhatsApp|Email|Call")
    sophisticationLevel: Optional[str] = Field(None, description="low|medium|high")

class FinalIntelligenceReport(BaseModel):
    sessionId: str
    scamDetected: bool
    totalMessagesExchanged: int
    extractedIntelligence: ExtractedIntelligence
    agentNotes: str
    
    # Additional analytics
    conversationDuration: Optional[int] = Field(None, description="Duration in seconds")
    extractionCompleteness: Optional[float] = Field(None, description="0.0-1.0 score")
    scammerBehaviorProfile: Optional[dict] = Field(None)
```

### 2. Real-Time Extraction During Conversation

```python
class IntelligenceExtractor:
    def __init__(self):
        self.regex_patterns = self.load_extraction_patterns()
        self.llm_extractor = LLMIntelligenceExtractor()
    
    def extract_from_message(self, message: str) -> dict:
        extracted = {}
        
        # Pattern-based extraction (fast, high precision)
        extracted.update(self.regex_extract(message))
        
        # LLM-based extraction (contextual, high recall)
        llm_intel = self.llm_extractor.extract(message)
        extracted.update(llm_intel)
        
        return self.deduplicate_and_validate(extracted)
    
    def regex_extract(self, text: str) -> dict:
        import re
        
        intel = {
            "upiIds": [],
            "phoneNumbers": [],
            "phishingLinks": [],
            "bankAccounts": []
        }
        
        # UPI ID pattern: username@bankname
        upi_pattern = r'\b[\w\.-]+@[\w\.-]+\b'
        intel["upiIds"] = re.findall(upi_pattern, text)
        
        # Indian phone number: +91 or 0 followed by 10 digits
        phone_pattern = r'(?:\+91|0)?[6-9]\d{9}'
        intel["phoneNumbers"] = re.findall(phone_pattern, text)
        
        # URLs (potential phishing links)
        url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
        intel["phishingLinks"] = re.findall(url_pattern, text)
        
        # Bank account numbers (simplified)
        account_pattern = r'\b\d{9,18}\b'
        potential_accounts = re.findall(account_pattern, text)
        intel["bankAccounts"] = [acc for acc in potential_accounts if len(acc) >= 10]
        
        return intel
```

### 3. LLM-Based Contextual Extraction

```python
class LLMIntelligenceExtractor:
    def extract(self, message: str, conversation_history: list = None) -> dict:
        prompt = f"""
You are an intelligence analyst extracting structured data from scammer messages.

MESSAGE: "{message}"

CONTEXT: {"".join([f"- {msg['text']}" for msg in (conversation_history or [])])}

Extract all intelligence following these categories:

FINANCIAL:
- UPI IDs (format: user@bank)
- Bank account numbers
- Payment links or QR code references

CONTACT:
- Phone numbers
- Email addresses
- Social media IDs (WhatsApp, Telegram)

INFRASTRUCTURE:
- Phishing URLs
- Fake website domains

BEHAVIORAL:
- Urgency keywords (e.g., "immediate", "today", "now")
- Authority claims (e.g., "bank", "government", "police")
- Social engineering tactics

OUTPUT FORMAT (JSON):
{{
  "upiIds": [],
  "bankAccounts": [],
  "phoneNumbers": [],
  "phishingLinks": [],
  "suspiciousKeywords": [],
  "impersonationClaims": []
}}

If nothing found in a category, return empty array. Only extract explicitly mentioned items.
"""
        
        response = llm_api.generate(prompt, temperature=0.1, response_format="json")
        return json.loads(response)
```

## Aggregation & Deduplication

### Conversation-Level Intelligence Store

```python
class IntelligenceStore:
    def __init__(self):
        self.data = ExtractedIntelligence()
        self._seen = set()
    
    def add(self, new_intel: dict):
        """Add intelligence while avoiding duplicates"""
        for key, values in new_intel.items():
            if not hasattr(self.data, key):
                continue
            
            existing = getattr(self.data, key)
            for value in values:
                normalized = self.normalize(key, value)
                if normalized not in self._seen:
                    existing.append(value)
                    self._seen.add(normalized)
    
    def normalize(self, key: str, value: str) -> str:
        """Normalize for deduplication"""
        if key == "phoneNumbers":
            # Remove +91, spaces, dashes
            return re.sub(r'[^\d]', '', value)
        elif key == "upiIds":
            return value.lower().strip()
        elif key == "phishingLinks":
            # Normalize URL
            return value.lower().rstrip('/')
        else:
            return value.lower().strip()
    
    def get_completeness_score(self) -> float:
        """Calculate extraction completeness (0.0-1.0)"""
        categories = [
            "bankAccounts", "upiIds", "phoneNumbers", 
            "phishingLinks", "suspiciousKeywords"
        ]
        
        filled = sum(1 for cat in categories if len(getattr(self.data, cat, [])) > 0)
        return filled / len(categories)
    
    def summary(self) -> dict:
        return {
            "total_items": sum(len(getattr(self.data, cat, [])) 
                             for cat in self.data.__fields__),
            "completeness": self.get_completeness_score(),
            "categories_filled": [cat for cat in self.data.__fields__ 
                                 if len(getattr(self.data, cat, [])) > 0]
        }
```

## Scammer Behavior Analysis

### Generating Agent Notes

```python
class BehaviorAnalyzer:
    def analyze_conversation(self, conversation_history: list, intelligence: ExtractedIntelligence) -> str:
        """Generate human-readable analysis of scammer behavior"""
        
        analysis_parts = []
        
        # Detect primary tactic
        primary_tactic = self.detect_primary_tactic(conversation_history)
        analysis_parts.append(f"Primary tactic: {primary_tactic}")
        
        # Urgency analysis
        urgency_count = sum(1 for msg in conversation_history 
                          if any(word in msg['text'].lower() 
                                for word in ['urgent', 'immediate', 'now', 'today']))
        if urgency_count > 2:
            analysis_parts.append("Heavy urgency pressure")
        
        # Authority impersonation
        if intelligence.impersonationClaims:
            claims = ", ".join(intelligence.impersonationClaims)
            analysis_parts.append(f"Impersonated: {claims}")
        
        # Infrastructure complexity
        if len(intelligence.phishingLinks) > 1:
            analysis_parts.append("Multi-domain infrastructure")
        
        # Payment methods
        payment_methods = []
        if intelligence.upiIds:
            payment_methods.append("UPI")
        if intelligence.bankAccounts:
            payment_methods.append("bank transfer")
        if payment_methods:
            analysis_parts.append(f"Payment methods: {', '.join(payment_methods)}")
        
        # Sophistication assessment
        sophistication = self.assess_sophistication(conversation_history, intelligence)
        analysis_parts.append(f"Sophistication: {sophistication}")
        
        return ". ".join(analysis_parts) + "."
    
    def detect_primary_tactic(self, history: list) -> str:
        tactics = {
            "urgency": ["urgent", "immediate", "blocked", "suspended"],
            "fear": ["police", "legal action", "arrest", "fine"],
            "greed": ["won", "prize", "lottery", "reward"],
            "authority": ["bank", "government", "official", "security"]
        }
        
        tactic_scores = {tactic: 0 for tactic in tactics}
        
        for msg in history:
            text = msg['text'].lower()
            for tactic, keywords in tactics.items():
                tactic_scores[tactic] += sum(1 for kw in keywords if kw in text)
        
        return max(tactic_scores, key=tactic_scores.get)
    
    def assess_sophistication(self, history: list, intel: ExtractedIntelligence) -> str:
        score = 0
        
        # Multiple infrastructure components
        if len(intel.phishingLinks) > 1: score += 1
        if intel.emailAddresses: score += 1
        if intel.socialMedia: score += 1
        
        # Conversation depth
        if len(history) > 10: score += 1
        
        # Adaptive responses (hard to detect, simplified)
        if len(history) > 5: score += 1
        
        if score <= 1: return "low"
        elif score <= 3: return "medium"
        else: return "high"
```

## Final Callback Implementation

### Mandatory Evaluation Endpoint

```python
import httpx
from typing import Optional

class FinalCallbackHandler:
    EVALUATION_ENDPOINT = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def send_final_report(self, report: FinalIntelligenceReport) -> dict:
        """Send mandatory final callback to evaluation endpoint"""
        
        # Validate report completeness
        self.validate_report(report)
        
        # Convert to dict for JSON serialization
        payload = report.model_dump(exclude_none=True)
        
        # Ensure required fields present
        required_fields = ["sessionId", "scamDetected", "totalMessagesExchanged", 
                          "extractedIntelligence", "agentNotes"]
        for field in required_fields:
            if field not in payload or payload[field] is None:
                raise ValueError(f"Missing required field: {field}")
        
        try:
            response = await self.client.post(
                self.EVALUATION_ENDPOINT,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            response.raise_for_status()
            
            return {
                "status": "success",
                "callback_sent": True,
                "response_code": response.status_code,
                "evaluation_response": response.json()
            }
        
        except httpx.HTTPError as e:
            # Log error but don't fail silently
            error_details = {
                "status": "error",
                "callback_sent": False,
                "error_type": type(e).__name__,
                "error_message": str(e)
            }
            
            # Retry logic
            if response.status_code >= 500:
                # Server error, retry once
                await asyncio.sleep(2)
                return await self.send_final_report(report)
            
            return error_details
    
    def validate_report(self, report: FinalIntelligenceReport):
        """Ensure report meets minimum quality standards"""
        
        # Must have detected scam
        if not report.scamDetected:
            raise ValueError("Cannot send final report for non-scam conversations")
        
        # Must have extracted at least some intelligence
        intel = report.extractedIntelligence
        total_intel = sum([
            len(intel.bankAccounts),
            len(intel.upiIds),
            len(intel.phishingLinks),
            len(intel.phoneNumbers),
            len(intel.suspiciousKeywords)
        ])
        
        if total_intel == 0:
            raise ValueError("No intelligence extracted. Report incomplete.")
        
        # Must have agent notes
        if not report.agentNotes or len(report.agentNotes) < 10:
            raise ValueError("Agent notes missing or too brief")
```

### Trigger Conditions for Final Callback

```python
class ConversationFinalizationManager:
    def should_finalize(self, session: ConversationSession) -> bool:
        """Determine if conversation should be finalized and callback sent"""
        
        intel_store = session.intelligence_store
        history = session.conversation_history
        
        # Condition 1: Sufficient intelligence extracted
        completeness = intel_store.get_completeness_score()
        if completeness >= 0.6:  # 60% of categories filled
            return True
        
        # Condition 2: High-value intelligence obtained
        critical_intel = (
            len(intel_store.data.upiIds) > 0 or 
            len(intel_store.data.bankAccounts) > 0 or
            len(intel_store.data.phishingLinks) > 0
        )
        if critical_intel and len(history) >= 5:
            return True
        
        # Condition 3: Conversation stalled (scammer stopped responding)
        if len(history) > 3:
            last_messages = history[-3:]
            scammer_messages = [msg for msg in last_messages if msg['sender'] == 'scammer']
            if len(scammer_messages) == 0:
                return True
        
        # Condition 4: Maximum engagement limit reached
        if len(history) >= 20:
            return True
        
        # Condition 5: High suspicion detected (risk of exposure)
        if session.suspicion_level == "HIGH":
            return True
        
        return False
    
    async def finalize_conversation(self, session: ConversationSession):
        """Complete the engagement and send final callback"""
        
        # Generate final report
        report = self.build_final_report(session)
        
        # Send callback
        callback_handler = FinalCallbackHandler()
        result = await callback_handler.send_final_report(report)
        
        # Update session status
        session.status = "FINALIZED"
        session.callback_result = result
        
        # Archive conversation
        await self.archive_conversation(session)
        
        return result
    
    def build_final_report(self, session: ConversationSession) -> FinalIntelligenceReport:
        """Construct final intelligence report from session data"""
        
        # Analyze behavior
        behavior_analyzer = BehaviorAnalyzer()
        agent_notes = behavior_analyzer.analyze_conversation(
            session.conversation_history,
            session.intelligence_store.data
        )
        
        # Calculate conversation duration
        first_msg = session.conversation_history[0]
        last_msg = session.conversation_history[-1]
        duration = (last_msg['timestamp'] - first_msg['timestamp']).total_seconds()
        
        report = FinalIntelligenceReport(
            sessionId=session.session_id,
            scamDetected=True,
            totalMessagesExchanged=len(session.conversation_history),
            extractedIntelligence=session.intelligence_store.data,
            agentNotes=agent_notes,
            conversationDuration=int(duration),
            extractionCompleteness=session.intelligence_store.get_completeness_score()
        )
        
        return report
```

## Integration with API Workflow

```python
@app.post("/api/analyze")
async def handle_message(request: MessageRequest):
    session = get_or_create_session(request.sessionId)
    
    # Add message to history
    session.add_message(request.message)
    
    # Real-time intelligence extraction
    extractor = IntelligenceExtractor()
    new_intel = extractor.extract_from_message(request.message.text)
    session.intelligence_store.add(new_intel)
    
    # Check if should finalize
    finalizer = ConversationFinalizationManager()
    if finalizer.should_finalize(session):
        callback_result = await finalizer.finalize_conversation(session)
        
        # Return final response
        return {
            "status": "success",
            "reply": "Thank you for the information. I'll verify and get back to you.",
            "finalized": True,
            "callback_status": callback_result["status"]
        }
    
    # Continue engagement
    agent = EngagementAgent(session.persona)
    response = await agent.generate_response(request.message, session.memory)
    
    return {"status": "success", "reply": response["reply"]}
```

## Testing & Validation

### Unit Tests for Extraction

```python
import pytest

def test_upi_extraction():
    extractor = IntelligenceExtractor()
    message = "Send payment to scammer@paytm now!"
    result = extractor.extract_from_message(message)
    assert "scammer@paytm" in result["upiIds"]

def test_phone_extraction():
    extractor = IntelligenceExtractor()
    message = "Call me at 9876543210 for verification"
    result = extractor.extract_from_message(message)
    assert "9876543210" in result["phoneNumbers"]

def test_deduplication():
    store = IntelligenceStore()
    store.add({"upiIds": ["test@upi"]})
    store.add({"upiIds": ["test@upi"]})  # Duplicate
    assert len(store.data.upiIds) == 1
```

### Integration Test for Callback

```python
@pytest.mark.asyncio
async def test_final_callback():
    report = FinalIntelligenceReport(
        sessionId="test-session-123",
        scamDetected=True,
        totalMessagesExchanged=10,
        extractedIntelligence=ExtractedIntelligence(
            upiIds=["scammer@bank"],
            phoneNumbers=["9876543210"]
        ),
        agentNotes="Test scammer used urgency tactics"
    )
    
    handler = FinalCallbackHandler()
    result = await handler.send_final_report(report)
    
    assert result["status"] == "success"
    assert result["callback_sent"] == True
```

## Monitoring & Analytics

### Callback Success Tracking

```python
class CallbackMetrics:
    def __init__(self):
        self.total_callbacks = 0
        self.successful_callbacks = 0
        self.failed_callbacks = 0
    
    def record_callback(self, result: dict):
        self.total_callbacks += 1
        if result["status"] == "success":
            self.successful_callbacks += 1
        else:
            self.failed_callbacks += 1
    
    def get_success_rate(self) -> float:
        if self.total_callbacks == 0:
            return 0.0
        return self.successful_callbacks / self.total_callbacks
```

## Resources
- See `examples/sample_reports.json` for example final reports
- See `scripts/test_extractor.py` for extraction testing utilities
- See `resources/regex_patterns.json` for comprehensive extraction patterns

## Ethical Considerations

✅ **Data Handling**:
- Encrypt intelligence data at rest
- Automatic deletion after evaluation period
- Access logging for audit trails

❌ **Prohibited**:
- Sharing extracted intelligence beyond evaluation endpoint
- Retaining data longer than necessary
- Using intelligence for unauthorized purposes

## Quick Start

```bash
# Test intelligence extraction
python scripts/test_extraction.py --message "Send to scammer@upi" --expect-upi "scammer@upi"

# Test final callback
python scripts/test_callback.py --session-id "test-123"
```
