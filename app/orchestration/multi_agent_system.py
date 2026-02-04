"""Multi-Agent Detection System - Orchestrates specialized detection agents"""

import asyncio
from typing import Dict, List
from app.agents.detection.text_analyst import TextContentAnalyst
from app.agents.detection.link_checker import LinkSecurityChecker
from app.agents.detection.consensus import ConsensusDecisionAgent
from app.config import settings


class MultiAgentDetectionSystem:
    """
    Orchestrates multiple specialized agents for scam detection
    Implements parallel agent execution and consensus decision-making
    Based on MINERVA multi-agent architecture
    """
    
    def __init__(self):
        """Initialize all detection agents"""
        self.agents = {
            "text_analyst": TextContentAnalyst(),
            "link_checker": LinkSecurityChecker(),
            "consensus": ConsensusDecisionAgent(
                confidence_threshold=settings.confidence_threshold
            )
        }
        
        print(f"[MultiAgentDetectionSystem] Initialized with {len(self.agents)} agents")
    
    async def analyze_message(
        self, 
        message_text: str, 
        metadata: Dict = None,
        conversation_history: List[Dict] = None
    ) -> Dict:
        """
        Analyze message using all available agents in parallel
        
        Args:
            message_text: Text content to analyze
            metadata: Optional metadata about the message
            conversation_history: Optional conversation history
            
        Returns:
            Comprehensive detection result with consensus decision
        """
        print(f"[Detection] Analyzing message: {message_text[:50]}...")
        
        # Run agents in parallel for speed
        agent_tasks = [
            self.agents["text_analyst"].analyze(message_text),
            self.agents["link_checker"].analyze(message_text),
        ]
        
        # Execute all agents concurrently
        agent_results = await asyncio.gather(*agent_tasks, return_exceptions=True)
        
        # Filter out any exceptions (failed agents)
        valid_results = []
        for i, result in enumerate(agent_results):
            if isinstance(result, Exception):
                print(f"[Warning] Agent {i} failed: {result}")
            else:
                valid_results.append(result)
        
        # Aggregate with consensus agent
        consensus_result = self.agents["consensus"].aggregate(valid_results)
        
        # Classify scam type if detected
        scam_type = None
        if consensus_result["scam_detected"]:
            scam_type = self.agents["consensus"].classify_scam_type(
                consensus_result["all_indicators"],
                valid_results
            )
        
        # Build comprehensive result
        detection_result = {
            "scam_detected": consensus_result["scam_detected"],
            "scam_type": scam_type,
            "confidence": consensus_result["confidence"],
            "consensus_risk_score": consensus_result["consensus_risk_score"],
            "indicators": consensus_result["all_indicators"],
            "contributing_agents": consensus_result["contributing_agents"],
            "high_risk_agents": consensus_result.get("high_risk_agents", []),
            "agent_details": valid_results,
            "agent_breakdown": consensus_result.get("agent_breakdown", []),
            "threshold_used": consensus_result.get("threshold_used", settings.confidence_threshold)
        }
        
        # Log decision
        if detection_result["scam_detected"]:
            print(f"[Detection] ✅ SCAM DETECTED: {scam_type} (confidence: {detection_result['confidence']:.2f})")
        else:
            print(f"[Detection] ❌ No scam detected (risk score: {detection_result['consensus_risk_score']:.2f})")
        
        return detection_result
    
    async def extract_intelligence(self, message_text: str) -> Dict:
        """
        Extract intelligence entities from message
        
        Args:
            message_text: Text to extract from
            
        Returns:
            Extracted entities (UPI IDs, phones, accounts, URLs)
        """
        # Use text analyst for entity extraction
        entities = self.agents["text_analyst"].extract_entities(message_text)
        
        # Use link checker for URL extraction
        urls = self.agents["link_checker"].extract_urls(message_text)
        entities["urls"] = urls
        
        return entities
    
    def get_agent_status(self) -> Dict:
        """Get status of all agents"""
        return {
            "total_agents": len(self.agents),
            "active_agents": list(self.agents.keys()),
            "configuration": {
                "confidence_threshold": settings.confidence_threshold
            }
        }
