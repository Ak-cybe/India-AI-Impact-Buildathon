"""Quick test for text analyst"""
import asyncio
from app.agents.detection.text_analyst import TextContentAnalyst

async def test():
    analyst = TextContentAnalyst()
    
    msg1 = "URGENT: Your bank account will be blocked today. Send OTP immediately to verify."
    msg2 = "This is Income Tax Department. Legal action will be taken if payment not made within 24 hours."
    
    r1 = await analyst.analyze(msg1)
    r2 = await analyst.analyze(msg2)
    
    print(f"Bank fraud: risk_score={r1['risk_score']}, indicators={r1['indicators']}")
    print(f"Authority: risk_score={r2['risk_score']}, indicators={r2['indicators']}")

asyncio.run(test())
