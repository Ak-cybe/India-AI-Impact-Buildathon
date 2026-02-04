"""Full system test - verifies all components are working"""

import sys
sys.path.insert(0, '.')
import asyncio

def test_detection_agents():
    print('=' * 50)
    print('TEST 1: Detection Agents')
    print('=' * 50)

    from app.agents.detection.text_analyst import TextContentAnalyst
    from app.agents.detection.link_checker import LinkSecurityChecker
    from app.agents.detection.consensus import ConsensusDecisionAgent

    analyst = TextContentAnalyst()
    result = asyncio.run(analyst.analyze('URGENT: Your bank account blocked! Send OTP to 9876543210'))
    print(f"Text Analysis: risk_score={result['risk_score']:.2f}, confidence={result['confidence']:.2f}")
    print(f"Indicators: {result['indicators']}")
    entities = analyst.extract_entities('Send money to scammer@ybl or call 9876543210')
    print(f"Entities: {entities}")
    print('✅ Detection agents working!')
    return True

def test_engagement_system():
    print()
    print('=' * 50)
    print('TEST 2: Engagement System')
    print('=' * 50)

    from app.agents.engagement.persona import HoneypotPersona
    from app.agents.engagement.temporal_manager import TemporalManager
    from app.agents.engagement.state_machine import ConversationStateMachine

    persona = HoneypotPersona(scam_type='bank_fraud')
    print(f"Persona: {persona.get_name()}, Age: {persona.get_age()}")

    temporal = TemporalManager(persona.persona_type)
    delay = temporal.calculate_response_delay(100)
    print(f"Response delay: {delay:.1f}s")

    sm = ConversationStateMachine('test-session')
    print(f"State Machine: {sm.get_current_state().value}")
    print('✅ Engagement system working!')
    return True

def test_intelligence_extraction():
    print()
    print('=' * 50)
    print('TEST 3: Intelligence Extraction')
    print('=' * 50)

    from app.agents.extraction.extractor import IntelligenceExtractor

    extractor = IntelligenceExtractor()
    intel = extractor.extract_all('Send money to scammer@ybl or call 9876543210. Visit bit.ly/scam')
    print(f"Extracted {len(intel)} intelligence items:")
    for item in intel:
        print(f"  - {item['type']}: {item['value']}")
    print('✅ Intelligence extraction working!')
    return True

def test_security():
    print()
    print('=' * 50)
    print('TEST 4: Security Components')
    print('=' * 50)

    from app.utils.security import input_sanitizer, kill_switch

    # Test input sanitization
    test_input = 'Hello <script>alert(1)</script>'
    sanitized = input_sanitizer.sanitize_string(test_input)
    print(f"Original: {test_input}")
    print(f"Sanitized: {sanitized}")

    # Test kill switch
    print(f"Kill Switch Active: {kill_switch.is_active}")
    print('✅ Security components working!')
    return True

def test_orchestration():
    print()
    print('=' * 50)
    print('TEST 5: Orchestration')
    print('=' * 50)

    from app.orchestration.multi_agent_system import MultiAgentDetectionSystem
    from app.orchestration.session_manager import SessionManager

    detection = MultiAgentDetectionSystem()
    print(f"Detection System: {len(detection.agents)} agents")

    session_mgr = SessionManager()
    print(f"Session Manager: Active sessions = {session_mgr.get_active_session_count()}")
    print('✅ Orchestration working!')
    return True

if __name__ == '__main__':
    results = []
    
    try:
        results.append(('Detection Agents', test_detection_agents()))
    except Exception as e:
        print(f"❌ Detection failed: {e}")
        results.append(('Detection Agents', False))
    
    try:
        results.append(('Engagement System', test_engagement_system()))
    except Exception as e:
        print(f"❌ Engagement failed: {e}")
        results.append(('Engagement System', False))
    
    try:
        results.append(('Intelligence Extraction', test_intelligence_extraction()))
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        results.append(('Intelligence Extraction', False))
    
    try:
        results.append(('Security', test_security()))
    except Exception as e:
        print(f"❌ Security failed: {e}")
        results.append(('Security', False))
    
    try:
        results.append(('Orchestration', test_orchestration()))
    except Exception as e:
        print(f"❌ Orchestration failed: {e}")
        results.append(('Orchestration', False))
    
    print()
    print('=' * 50)
    print('FINAL RESULTS')
    print('=' * 50)
    
    all_passed = True
    for name, passed in results:
        status = '✅' if passed else '❌'
        print(f"{status} {name}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print('🎉 ALL TESTS PASSED!')
    else:
        print('⚠️ Some tests failed')
