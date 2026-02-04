"""Main FastAPI application for Agentic Honeypot API - Week 4 Complete (Production Ready)"""

from fastapi import FastAPI, Header, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import logging
import time

from app.config import settings
from app.models.request import MessageRequest, MessageResponse, ImageAnalysisRequest
from app.orchestration.multi_agent_system import MultiAgentDetectionSystem
from app.orchestration.session_manager import session_manager
from app.agents.extraction.callback import callback_handler
from app.utils.security import rate_limiter, input_sanitizer, kill_switch
from app.agents.detection.ocr_agent import initialize_ocr, ocr_agent, adversarial_detector

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Agentic Honeypot API",
    description="AI-powered scam detection, engagement, and intelligence extraction with mandatory callback. Week 4: Production-ready with security hardening.",
    version="4.0.0",  # Week 4 Complete - Production Ready
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global detection system instance
detection_system: Optional[MultiAgentDetectionSystem] = None


# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting to all requests"""
    # Skip rate limiting for health checks and static files
    if request.url.path in ["/", "/health", "/docs", "/redoc", "/openapi.json", "/favicon.ico"]:
        return await call_next(request)
    
    # Get API key from header (if present)
    api_key = request.headers.get("x-api-key")
    
    # Check rate limit
    is_allowed, details = rate_limiter.check_rate_limit(request, api_key)
    
    if not is_allowed:
        logger.warning(f"[RateLimit] Request blocked: {details}")
        import json
        return Response(
            content=json.dumps({"error": "rate_limited", "details": details}),
            status_code=429,
            media_type="application/json",
            headers={"Retry-After": str(details.get("retry_after", 60) if isinstance(details, dict) else 60)}
        )
    
    # Add rate limit headers to response
    response = await call_next(request)
    if isinstance(details, dict):
        response.headers["X-RateLimit-Remaining-Minute"] = str(details.get("remaining_minute", 0))
        response.headers["X-RateLimit-Remaining-Hour"] = str(details.get("remaining_hour", 0))
    
    return response


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize systems on startup"""
    global detection_system
    logger.info("🚀 Starting Agentic Honeypot API v4.0 (Production Ready)...")
    
    # Initialize multi-agent detection system
    detection_system = MultiAgentDetectionSystem()
    
    # Initialize OCR agent (Week 4)
    initialize_ocr(settings.google_api_key)
    
    logger.info(f"✅ Detection system: {len(detection_system.agents)} agents")
    logger.info(f"✅ Session manager: Ready")
    logger.info(f"✅ OCR Agent: {'Available' if ocr_agent and ocr_agent.is_available() else 'Not configured'}")
    logger.info(f"✅ Rate Limiter: Active")
    logger.info(f"✅ Kill Switch: {'Active' if kill_switch.is_active else 'PAUSED'}")
    logger.info(f"📡 Server: {settings.api_host}:{settings.api_port}")


# Authentication dependency
async def verify_api_key(x_api_key: str = Header(...)):
    """Verify API key from header"""
    if x_api_key != settings.api_key:
        logger.warning(f"Invalid API key attempted: {x_api_key[:10]}...")
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


# Admin authentication (stricter)
async def verify_admin_key(x_admin_key: str = Header(...)):
    """Verify admin key for management endpoints"""
    admin_key = getattr(settings, 'admin_key', settings.api_key + "-admin")
    if x_admin_key != admin_key:
        raise HTTPException(status_code=403, detail="Admin access required")
    return x_admin_key


@app.get("/favicon.ico")
async def favicon():
    """Return empty response for favicon"""
    return Response(content=b"", media_type="image/x-icon")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online" if kill_switch.is_active else "paused",
        "service": "Agentic Honeypot API",
        "version": "4.0.0",
        "detection_agents": len(detection_system.agents) if detection_system else 0,
        "active_sessions": session_manager.get_active_session_count(),
        "kill_switch": kill_switch.get_status()
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    if not detection_system:
        raise HTTPException(status_code=503, detail="Detection system not initialized")
    
    agent_status = detection_system.get_agent_status()
    
    return {
        "status": "healthy",
        "components": {
            "detection_system": agent_status,
            "session_manager": session_manager.get_all_sessions_summary()
        },
        "configuration": {
            "environment": settings.environment,
            "max_conversation_turns": settings.max_conversation_turns,
            "confidence_threshold": settings.confidence_threshold
        }
    }


@app.post("/api/analyze", response_model=MessageResponse)
async def analyze_message(
    request: MessageRequest,
    api_key: str = Depends(verify_api_key)
) -> MessageResponse:
    """
    Main endpoint for message analysis and engagement
    
    Flow:
    1. Detect scam intent using multi-agent system
    2. If scam detected, create/get engagement session
    3. Generate persona-based response
    4. Extract intelligence from scammer's message
    5. Return response with session status
    """
    logger.info(f"📨 Request for session: {request.sessionId}")
    
    if not detection_system:
        raise HTTPException(status_code=503, detail="Detection system not initialized")
    
    try:
        message_text = request.message.text
        platform = request.metadata.channel if request.metadata else "sms"
        
        # Check if this is a continuing session
        existing_session = session_manager.get_session(request.sessionId)
        
        if existing_session:
            # Continuing conversation - skip detection, go straight to engagement
            logger.info(f"📞 Continuing session {request.sessionId}")
            
            # Process message with engagement agent
            engagement_result = await existing_session.process_message(
                scammer_message=message_text,
                metadata=request.metadata.model_dump() if request.metadata else None,
                apply_delay=False  # Don't actually wait in API (handle async in production)
            )
            
            # Check if session should end
            if not engagement_result.get("session_active", True):
                # Complete the session
                report = session_manager.complete_session(request.sessionId)
                logger.info(f"📊 Session {request.sessionId} completed")
                
                return MessageResponse(
                    status="session_complete",
                    reply=engagement_result.get("response"),
                    scam_detected=True,
                    session_active=False,
                    intelligence_count=report.get("intelligence", {}).get("count", 0)
                )
            
            return MessageResponse(
                status="success",
                reply=engagement_result.get("response"),
                scam_detected=True,
                session_active=engagement_result.get("session_active", True),
                intelligence_count=engagement_result.get("intelligence_count", 0)
            )
        
        # New message - run detection first
        detection_result = await detection_system.analyze_message(
            message_text=message_text,
            metadata=request.metadata.model_dump() if request.metadata else None,
            conversation_history=request.conversationHistory
        )
        
        # HACKATHON FIX: Force detection for obvious scam keywords
        scam_keywords = ["otp", "urgent", "blocked", "upi", "bank", "account", "transfer", "payment", "verify", "kyc"]
        has_scam_keyword = any(kw in message_text.lower() for kw in scam_keywords)
        
        if detection_result["scam_detected"] or has_scam_keyword:
            scam_type = detection_result.get("scam_type") or "bank_fraud"
            logger.info(f"🚨 Scam detected: {scam_type} (keyword_match: {has_scam_keyword})")
            
            # Create new engagement session
            agent = session_manager.create_session(
                session_id=request.sessionId,
                scam_type=scam_type,
                platform=platform
            )
            
            # Generate first response
            engagement_result = await agent.process_message(
                scammer_message=message_text,
                metadata=request.metadata.model_dump() if request.metadata else None,
                apply_delay=False
            )
            
            return MessageResponse(
                status="success",
                reply=engagement_result.get("response"),
                scam_detected=True,
                session_active=True,
                intelligence_count=engagement_result.get("intelligence_count", 0)
            )
        else:
            logger.info("✅ No scam detected - legitimate message")
            
            return MessageResponse(
                status="success",
                reply=None,  # No engagement for legitimate messages
                scam_detected=False,
                session_active=False,
                intelligence_count=0
            )
    
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/api/session/{session_id}")
async def get_session_status(
    session_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get detailed status of a session"""
    summary = session_manager.get_session_summary(session_id)
    
    if not summary:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    return summary


@app.get("/api/sessions")
async def list_sessions(
    api_key: str = Depends(verify_api_key)
):
    """List all active and completed sessions"""
    return session_manager.get_all_sessions_summary()


@app.post("/api/session/{session_id}/complete")
async def complete_session(
    session_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Manually complete a session and get final report"""
    report = session_manager.complete_session(session_id)
    
    if "error" in report:
        raise HTTPException(status_code=404, detail=report["error"])
    
    return {
        "status": "completed",
        "report": report
    }


@app.get("/api/session/{session_id}/report")
async def get_session_report(
    session_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get full report for a session (for callback preparation)"""
    agent = session_manager.get_session(session_id)
    
    if not agent:
        # Check completed sessions
        completed = session_manager.completed_sessions.get(session_id)
        if completed:
            return completed
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    return agent.get_session_report()


@app.post("/api/session/{session_id}/callback")
async def send_session_callback(
    session_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Send final intelligence to evaluation endpoint (MANDATORY)
    
    This is the required callback to:
    https://hackathon.guvi.in/api/updateHoneyPotFinalResult
    
    Requirements:
    - Minimum 3 intelligence items
    - Valid session with conversation history
    """
    # Get session
    agent = session_manager.get_session(session_id)
    
    if not agent:
        # Check if already completed (callback already sent)
        completed = session_manager.completed_sessions.get(session_id)
        if completed:
            return {
                "status": "already_submitted",
                "session_id": session_id,
                "message": "Callback was already sent for this session"
            }
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    # Send callback
    result = await callback_handler.send_final_report(agent)
    
    if result["success"]:
        # Mark session as completed
        session_manager.complete_session(session_id)
        
        logger.info(f"✅ Callback successful for session {session_id}")
        return {
            "status": "success",
            "session_id": session_id,
            "callback_result": result,
            "message": "Intelligence successfully reported to evaluation endpoint"
        }
    else:
        logger.error(f"❌ Callback failed for session {session_id}: {result}")
        return {
            "status": "failed",
            "session_id": session_id,
            "error": result.get("error"),
            "reason": result.get("reason"),
            "message": "Failed to send callback - see error details"
        }


@app.post("/api/callback/batch")
async def send_batch_callbacks(
    api_key: str = Depends(verify_api_key)
):
    """
    Send callbacks for all completed sessions that haven't been reported yet
    
    Useful for batch processing at end of evaluation
    """
    results = []
    
    # Get all active sessions
    for session_id, agent in list(session_manager.sessions.items()):
        # Check if session is ready for callback
        if len(agent.intelligence_items) >= 3:
            result = await callback_handler.send_final_report(agent)
            results.append({
                "session_id": session_id,
                "success": result["success"],
                "intelligence_count": len(agent.intelligence_items)
            })
            
            if result["success"]:
                session_manager.complete_session(session_id)
    
    return {
        "total_processed": len(results),
        "successful": sum(1 for r in results if r["success"]),
        "failed": sum(1 for r in results if not r["success"]),
        "results": results
    }


# ========================================
# Week 4: OCR / Image Analysis Endpoints
# ========================================

@app.post("/api/analyze/image")
async def analyze_image(
    request: ImageAnalysisRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Analyze image for scam detection (Week 4 Feature)
    
    Extracts text from images using OCR and analyzes for scam indicators.
    Supports: Screenshots, QR codes, forwarded images
    """
    if not kill_switch.is_active:
        raise HTTPException(status_code=503, detail="System is paused")
    
    if not ocr_agent or not ocr_agent.is_available():
        raise HTTPException(
            status_code=503, 
            detail="OCR agent not available. Install pytesseract or configure Gemini API."
        )
    
    try:
        # Process image
        result = ocr_agent.extract_text_from_base64(
            request.image_base64,
            backend=request.backend or "auto"
        )
        
        if result["success"]:
            # If scam indicators found, we could optionally create engagement session
            return {
                "status": "success",
                "extracted_text": result["raw_text"],
                "intelligence": result["intelligence"],
                "is_scam_likely": result["is_scam_likely"],
                "backend_used": result["backend"]
            }
        else:
            return {
                "status": "failed",
                "error": result.get("error"),
                "message": result.get("message")
            }
            
    except Exception as e:
        logger.error(f"Image analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")


@app.post("/api/analyze/adversarial")
async def check_adversarial(
    messages: list,
    timings: list = None,
    api_key: str = Depends(verify_api_key)
):
    """
    Check if scammer is using AI-generated responses (Week 4 Feature)
    
    Analyzes message patterns to detect automated/AI scammers.
    """
    if not messages:
        raise HTTPException(status_code=400, detail="No messages provided")
    
    result = adversarial_detector.analyze_conversation(messages, timings)
    
    return {
        "status": "success",
        "is_likely_ai": result["is_likely_ai"],
        "ai_probability": result["ai_probability"],
        "recommendation": result["recommendation"],
        "analysis": result
    }


# ========================================
# Week 4: Admin / Management Endpoints
# ========================================

@app.post("/admin/kill-switch/pause")
async def pause_system(
    reason: str = "Manual pause",
    admin_key: str = Depends(verify_admin_key)
):
    """
    Emergency pause - stops all honeypot engagement
    
    Use this to immediately halt all operations if needed.
    """
    result = kill_switch.pause_system(reason)
    logger.warning(f"🛑 ADMIN: System paused - {reason}")
    return result


@app.post("/admin/kill-switch/resume")
async def resume_system(
    admin_key: str = Depends(verify_admin_key)
):
    """Resume honeypot operations after pause"""
    result = kill_switch.resume_system()
    logger.info("✅ ADMIN: System resumed")
    return result


@app.post("/admin/kill-switch/session/{session_id}")
async def kill_session(
    session_id: str,
    reason: str = "Manual termination",
    admin_key: str = Depends(verify_admin_key)
):
    """Immediately terminate a specific session"""
    result = kill_switch.kill_session(session_id, reason)
    
    # Also remove from session manager
    session_manager.complete_session(session_id)
    
    return result


@app.get("/admin/status")
async def admin_status(
    admin_key: str = Depends(verify_admin_key)
):
    """Get full system status for admin"""
    return {
        "kill_switch": kill_switch.get_status(),
        "rate_limiter": {
            "tracked_clients": len(rate_limiter.request_log),
            "blocked_clients": len(rate_limiter.blocklist)
        },
        "sessions": session_manager.get_all_sessions_summary(),
        "detection_system": detection_system.get_agent_status() if detection_system else None,
        "ocr_available": ocr_agent.is_available() if ocr_agent else False
    }


@app.get("/admin/rate-limits")
async def get_rate_limits(
    admin_key: str = Depends(verify_admin_key)
):
    """View current rate limiting status"""
    return {
        "config": {
            "requests_per_minute": rate_limiter.config.requests_per_minute,
            "requests_per_hour": rate_limiter.config.requests_per_hour,
            "burst_limit": rate_limiter.config.burst_limit,
            "block_duration_minutes": rate_limiter.config.block_duration_minutes
        },
        "current_state": {
            "tracked_clients": len(rate_limiter.request_log),
            "blocked_clients": list(rate_limiter.blocklist.keys())[:10]  # First 10
        }
    }


@app.post("/admin/rate-limits/unblock/{identifier}")
async def unblock_client(
    identifier: str,
    admin_key: str = Depends(verify_admin_key)
):
    """Manually unblock a rate-limited client"""
    if identifier in rate_limiter.blocklist:
        del rate_limiter.blocklist[identifier]
        return {"status": "unblocked", "identifier": identifier}
    return {"status": "not_found", "identifier": identifier}


# ========================================
# Error handlers
# ========================================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"error": "Endpoint not found", "detail": str(exc)}


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal error: {exc}", exc_info=True)
    return {"error": "Internal server error", "detail": "Please contact support"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True if settings.environment == "development" else False,
        log_level=settings.log_level.lower()
    )

