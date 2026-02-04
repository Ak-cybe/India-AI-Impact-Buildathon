"""Tests for intelligence extraction and callback system"""

import pytest
import asyncio

# Import test subjects
import sys
sys.path.insert(0, 'c:\\Users\\Acer\\Desktop\\lab\\Hackathon Challenge')

from app.agents.extraction.extractor import IntelligenceExtractor
from app.agents.extraction.callback import CallbackHandler


class TestIntelligenceExtractor:
    """Test intelligence extraction patterns"""
    
    def setup_method(self):
        """Setup extractor for each test"""
        self.extractor = IntelligenceExtractor()
    
    def test_upi_id_extraction(self):
        """Test UPI ID extraction"""
        text = "Please send money to scammer123@ybl or fraud456@paytm immediately"
        
        intel = self.extractor.extract_all(text)
        
        upi_items = [i for i in intel if i["type"] == "upi_id"]
        assert len(upi_items) == 2
        assert any("scammer123@ybl" in i["value"] for i in upi_items)
        assert any("fraud456@paytm" in i["value"] for i in upi_items)
    
    def test_upi_id_various_providers(self):
        """Test UPI extraction for various providers"""
        text = """
        Send to: 
        user@okaxis
        victim@okicici  
        target@okhdfcbank
        money@sbi
        cash@hdfc
        """
        
        intel = self.extractor.extract_all(text)
        upi_items = [i for i in intel if i["type"] == "upi_id"]
        
        assert len(upi_items) >= 4  # Should catch most providers
    
    def test_phone_number_extraction_indian(self):
        """Test Indian phone number extraction"""
        text = "Call me at 9876543210 or +91 8765432109 urgently"
        
        intel = self.extractor.extract_all(text)
        
        phone_items = [i for i in intel if i["type"] == "phone_number"]
        assert len(phone_items) >= 1
    
    def test_phone_number_with_spaces(self):
        """Test phone number with country code"""
        text = "My number is +919876543210 or 8765432109"
        
        intel = self.extractor.extract_all(text)
        
        phone_items = [i for i in intel if i["type"] == "phone_number"]
        assert len(phone_items) >= 1
    
    def test_url_extraction(self):
        """Test URL extraction"""
        text = "Click this link: https://scam-site.com/verify?user=123 to verify your account"
        
        intel = self.extractor.extract_all(text)
        
        url_items = [i for i in intel if i["type"] == "url"]
        assert len(url_items) == 1
        assert "scam-site.com" in url_items[0]["value"]
    
    def test_shortened_url_detection(self):
        """Test shortened URL detection and risk flagging"""
        text = "Visit bit.ly/scam123 for more info"
        
        intel = self.extractor.extract_all(text)
        
        url_items = [i for i in intel if i["type"] == "url"]
        assert len(url_items) >= 1
        # Shortened URLs should be flagged as high risk
        assert any(i.get("is_shortened") or i.get("risk") == "high" for i in url_items)
    
    def test_email_extraction(self):
        """Test email extraction (excluding UPI IDs)"""
        text = "Contact us at support@scamcompany.com for help"
        
        intel = self.extractor.extract_all(text)
        
        email_items = [i for i in intel if i["type"] == "email"]
        assert len(email_items) == 1
        assert "support@scamcompany.com" in email_items[0]["value"]
    
    def test_bank_account_extraction(self):
        """Test bank account number extraction"""
        text = "Transfer money to account number 12345678901234"
        
        intel = self.extractor.extract_all(text)
        
        account_items = [i for i in intel if i["type"] == "bank_account"]
        assert len(account_items) >= 1
    
    def test_ifsc_code_extraction(self):
        """Test IFSC code extraction"""
        text = "Bank IFSC code is SBIN0001234 for the branch"
        
        intel = self.extractor.extract_all(text)
        
        ifsc_items = [i for i in intel if i["type"] == "ifsc_code"]
        assert len(ifsc_items) == 1
        assert ifsc_items[0]["value"] == "SBIN0001234"
    
    def test_crypto_wallet_btc(self):
        """Test Bitcoin wallet address extraction"""
        text = "Send BTC to 1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"
        
        intel = self.extractor.extract_all(text)
        
        crypto_items = [i for i in intel if i["type"] == "crypto_wallet_btc"]
        assert len(crypto_items) == 1
    
    def test_crypto_wallet_eth(self):
        """Test Ethereum wallet address extraction"""
        text = "ETH address: 0x742d35Cc6634C0532925a3b844Bc9e7595f9ABCD"
        
        intel = self.extractor.extract_all(text)
        
        crypto_items = [i for i in intel if i["type"] == "crypto_wallet_eth"]
        assert len(crypto_items) == 1
    
    def test_scam_app_detection(self):
        """Test scam app mention detection"""
        text = "Please download AnyDesk app and share the code with me"
        
        intel = self.extractor.extract_all(text)
        
        app_items = [i for i in intel if i["type"] == "scam_app_mention"]
        assert len(app_items) == 1
        assert app_items[0]["value"] == "anydesk"
        assert app_items[0]["risk"] == "high"
    
    def test_bank_impersonation_detection(self):
        """Test bank impersonation claim detection"""
        text = "This is SBI Bank security calling about your account"
        
        intel = self.extractor.extract_all(text)
        
        org_items = [i for i in intel if i["type"] == "claimed_organization"]
        assert len(org_items) >= 1
        assert "SBI" in org_items[0]["value"]
    
    def test_complex_message_extraction(self):
        """Test extraction from complex scam message"""
        text = """
        URGENT: Your SBI account has been blocked!
        To reactivate, send Rs 1000 to fraud@ybl
        Or call +91 9876543210 immediately.
        Download TeamViewer from bit.ly/tv123 for remote assistance.
        Bank account for refund: 98765432109876
        """
        
        intel = self.extractor.extract_all(text)
        
        # Should find multiple intelligence items
        assert len(intel) >= 4
        
        types_found = {i["type"] for i in intel}
        assert "upi_id" in types_found
        assert "phone_number" in types_found
        assert "url" in types_found or "scam_app_mention" in types_found
    
    def test_deduplication(self):
        """Test duplicate removal"""
        items = [
            {"type": "upi_id", "value": "test@ybl", "confidence": 0.9},
            {"type": "upi_id", "value": "test@ybl", "confidence": 0.9},  # Duplicate
            {"type": "phone_number", "value": "9876543210", "confidence": 0.8},
        ]
        
        unique = self.extractor.deduplicate_intelligence(items)
        
        assert len(unique) == 2
    
    def test_high_confidence_filter(self):
        """Test confidence threshold filtering"""
        items = [
            {"type": "upi_id", "value": "test@ybl", "confidence": 0.9},
            {"type": "bank_account", "value": "12345", "confidence": 0.5},  # Low
            {"type": "phone_number", "value": "9876543210", "confidence": 0.85},
        ]
        
        filtered = self.extractor.filter_high_confidence(items, threshold=0.75)
        
        assert len(filtered) == 2
    
    def test_summary_generation(self):
        """Test intelligence summary statistics"""
        items = [
            {"type": "upi_id", "value": "test@ybl", "confidence": 0.9, "risk": "high"},
            {"type": "phone_number", "value": "9876543210", "confidence": 0.8},
            {"type": "upi_id", "value": "other@paytm", "confidence": 0.85, "risk": "high"},
        ]
        
        summary = self.extractor.get_summary(items)
        
        assert summary["total_items"] == 3
        assert summary["by_type"]["upi_id"] == 2
        assert summary["by_type"]["phone_number"] == 1
        assert summary["high_risk_count"] == 2


class TestCallbackHandler:
    """Test callback handler"""
    
    def setup_method(self):
        """Setup callback handler for each test"""
        self.handler = CallbackHandler()
    
    def test_validation_insufficient_intelligence(self):
        """Test validation fails with less than 3 items"""
        intel = [
            {"type": "upi_id", "value": "test@ybl", "confidence": 0.9},
            {"type": "phone_number", "value": "9876543210", "confidence": 0.8},
        ]
        
        result = self.handler.validate_payload(intel)
        
        assert not result["valid"]
        assert "Insufficient" in result["reason"]
    
    def test_validation_sufficient_intelligence(self):
        """Test validation passes with 3+ items"""
        intel = [
            {"type": "upi_id", "value": "test@ybl", "confidence": 0.9},
            {"type": "phone_number", "value": "9876543210", "confidence": 0.8},
            {"type": "url", "value": "https://scam.com", "confidence": 0.85},
        ]
        
        result = self.handler.validate_payload(intel)
        
        assert result["valid"]
    
    def test_validation_no_high_value_items(self):
        """Test validation fails without high-value items"""
        intel = [
            {"type": "scam_app_mention", "value": "anydesk", "confidence": 0.9},
            {"type": "claimed_organization", "value": "SBI", "confidence": 0.8},
            {"type": "claimed_organization", "value": "RBI", "confidence": 0.7},
        ]
        
        result = self.handler.validate_payload(intel)
        
        assert not result["valid"]
        assert "high-value" in result["reason"].lower()
    
    def test_validation_low_confidence(self):
        """Test validation fails with low average confidence"""
        intel = [
            {"type": "upi_id", "value": "test@ybl", "confidence": 0.3},
            {"type": "phone_number", "value": "9876543210", "confidence": 0.4},
            {"type": "url", "value": "https://scam.com", "confidence": 0.2},
        ]
        
        result = self.handler.validate_payload(intel)
        
        assert not result["valid"]
        assert "confidence" in result["reason"].lower()
    
    def test_payload_building(self):
        """Test callback payload structure"""
        intel = [
            {"type": "upi_id", "value": "test@ybl", "confidence": 0.9},
        ]
        conversation = [
            {"role": "scammer", "message": "Send OTP"},
            {"role": "agent", "message": "Kya?"},
        ]
        
        payload = self.handler._build_payload(
            session_id="test-123",
            scam_type="bank_fraud",
            intelligence=intel,
            conversation=conversation,
            confidence=0.85
        )
        
        assert payload["sessionId"] == "test-123"
        assert payload["scamType"] == "bank_fraud"
        assert len(payload["intelligenceGathered"]) == 1
        assert len(payload["conversationTranscript"]) == 2
        assert "metadata" in payload


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
