"""Consensus Decision Agent - Aggregates results from specialized agents"""

from typing import Dict, List


class ConsensusDecisionAgent:
    """
    Aggregates results from multiple specialized detection agents
    Uses weighted voting based on agent confidence scores
    Based on MINERVA framework decision-making component
    """
    
    def __init__(self, confidence_threshold: float = 0.1):
        """
        Initialize consensus agent
        
        Args:
            confidence_threshold: Minimum consensus score to classify as scam
        """
        self.confidence_threshold = confidence_threshold
        
        # Agent weights (can be tuned based on performance)
        self.agent_weights = {
            "text_analyst": 1.0,
            "link_checker": 1.2,  # Slightly higher weight - links are strong indicators
            "ocr_agent": 1.0,
            "adversarial_detector": 0.8,  # Lower weight - more experimental
        }
    
    def aggregate(self, agent_results: List[Dict]) -> Dict:
        """
        Aggregate results from multiple agents using weighted voting
        
        Args:
            agent_results: List of results from each agent
            
        Returns:
            Aggregated decision with consensus metrics
        """
        if not agent_results:
            return {
                "scam_detected": False,
                "consensus_risk_score": 0.0,
                "confidence": 0.0,
                "contributing_agents": [],
                "all_indicators": [],
                "agent_breakdown": []
            }
        
        total_risk = 0.0
        total_weight = 0.0
        all_indicators = []
        agent_breakdown = []
        
        for result in agent_results:
            agent_name = result.get("agent", "unknown")
            confidence = result.get("confidence", 0.5)
            risk_score = result.get("risk_score", 0.0)
            
            # Get agent weight (default to 1.0 if not specified)
            weight = self.agent_weights.get(agent_name, 1.0)
            
            # Apply confidence weighting
            effective_weight = weight * confidence
            
            # Accumulate weighted risk
            total_risk += risk_score * effective_weight
            total_weight += effective_weight
            
            # Collect indicators
            if "indicators" in result:
                all_indicators.extend(result["indicators"])
            
            # Track agent contributions
            agent_breakdown.append({
                "agent": agent_name,
                "risk_score": risk_score,
                "confidence": confidence,
                "weight": weight,
                "effective_contribution": risk_score * effective_weight
            })
        
        # Calculate consensus risk score
        consensus_risk = total_risk / total_weight if total_weight > 0 else 0.0
        
        # Make binary decision
        scam_detected = consensus_risk > self.confidence_threshold
        
        # Calculate overall confidence (average of agent confidences)
        overall_confidence = sum(r.get("confidence", 0.5) for r in agent_results) / len(agent_results)
        
        # Deduplicate indicators
        unique_indicators = list(set(all_indicators))
        
        # Identify high-risk agents (those that flagged >0.7)
        high_risk_agents = [
            result.get("agent", "unknown") 
            for result in agent_results 
            if result.get("risk_score", 0.0) > 0.7
        ]
        
        return {
            "scam_detected": scam_detected,
            "consensus_risk_score": round(consensus_risk, 3),
            "confidence": round(overall_confidence, 3),
            "contributing_agents": [r.get("agent", "unknown") for r in agent_results],
            "high_risk_agents": high_risk_agents,
            "all_indicators": unique_indicators,
            "agent_breakdown": agent_breakdown,
            "total_agents": len(agent_results),
            "threshold_used": self.confidence_threshold
        }
    
    def classify_scam_type(self, indicators: List[str], agent_results: List[Dict]) -> str:
        """
        Classify the type of scam based on indicators
        
        Args:
            indicators: List of all detected indicators
            agent_results: Full agent results for context
            
        Returns:
            Scam type classification
        """
        # Check for specific scam patterns
        if "credential_request" in indicators:
            if any("bank" in str(r).lower() or "upi" in str(r).lower() for r in agent_results):
                return "bank_fraud"
            else:
                return "credential_phishing"
        
        if "malicious_link" in indicators:
            return "phishing_link"
        
        if "authority_impersonation" in indicators:
            if "threatening_language" in indicators:
                return "government_impersonation_scam"
            else:
                return "authority_scam"
        
        if "urgency_tactic" in indicators and "financial_identifiers_present" in indicators:
            return "payment_scam"
        
        # Default
        return "generic_scam"
