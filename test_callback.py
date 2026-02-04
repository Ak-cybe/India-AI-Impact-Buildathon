"""Test callback with empty intelligence"""
import asyncio
from app.agents.extraction.callback import CallbackHandler

async def test():
    handler = CallbackHandler()
    
    # Test with 0 intelligence items - should still attempt callback
    result = await handler.send_callback(
        session_id="test-001",
        scam_type="bank_fraud",
        intelligence=[],  # Empty!
        conversation=[{"role": "scammer", "message": "test"}],
        confidence=0.8
    )
    
    print(f"Result: {result}")
    if "success" in result:
        print("Callback WAS ATTEMPTED!")
    else:
        print("Callback NOT attempted - BUG!")

asyncio.run(test())
