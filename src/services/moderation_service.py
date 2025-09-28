"""
Content moderation service for user queries and AI responses
"""
import re
import os
from typing import Dict, Any, List, Tuple
from groq import Groq

class ModerationService:
    """Content moderation service using rule-based and Groq-based moderation"""
    
    def __init__(self):
        self.groq_client = None
        self._initialize_groq()
        self._load_moderation_rules()
    
    def _initialize_groq(self):
        """Initialize Groq client for AI-based moderation"""
        try:
            api_key = os.getenv("GROQ_API_KEY")
            if api_key:
                self.groq_client = Groq(api_key=api_key)
                print("SUCCESS: Groq moderation client initialized")
            else:
                print("WARNING: Groq API key not found. Using rule-based moderation only.")
        except Exception as e:
            print(f"ERROR: Failed to initialize Groq moderation: {e}")
    
    def _load_moderation_rules(self):
        """Load rule-based moderation patterns"""
        # Harmful content patterns
        self.harmful_patterns = [
            r'\b(?:kill|murder|suicide|harm|hurt|violence)\b',
            r'\b(?:illegal|crime|fraud|scam)\b',
            r'\b(?:hate|racist|discrimination)\b'
        ]
        
        # Legal advice warning patterns
        self.legal_advice_patterns = [
            r'\b(?:should i|what should|recommend|advise|tell me to)\b',
            r'\b(?:my case|my situation|my problem)\b',
            r'\b(?:sue|lawsuit|court|legal action)\b'
        ]
        
        # Inappropriate content patterns
        self.inappropriate_patterns = [
            r'\b(?:sexual|explicit|adult|nsfw)\b',
            r'\b(?:drug|illegal substance|narcotics)\b'
        ]
    
    async def moderate_user_query(self, query: str) -> Dict[str, Any]:
        """Moderate user query for safety and appropriateness"""
        result = {
            "is_safe": True,
            "warnings": [],
            "requires_disclaimer": False,
            "severity": "low",
            "filtered_query": query
        }
        
        # Rule-based moderation
        rule_result = self._rule_based_moderation(query)
        result.update(rule_result)
        
        # AI-based moderation if available
        if self.groq_client and result["is_safe"]:
            ai_result = await self._ai_based_moderation(query, "user_query")
            if not ai_result["is_safe"]:
                result.update(ai_result)
        
        return result
    
    async def moderate_ai_response(self, response: str, user_query: str = "") -> Dict[str, Any]:
        """Moderate AI response for safety and legal compliance"""
        result = {
            "is_safe": True,
            "warnings": [],
            "requires_disclaimer": False,
            "severity": "low",
            "filtered_response": response
        }
        
        # Check for legal advice patterns
        if self._contains_legal_advice(response):
            result["requires_disclaimer"] = True
            result["warnings"].append("Response may contain legal information")
        
        # AI-based moderation if available
        if self.groq_client:
            ai_result = await self._ai_based_moderation(response, "ai_response")
            if not ai_result["is_safe"]:
                result.update(ai_result)
        
        return result
    
    def _rule_based_moderation(self, text: str) -> Dict[str, Any]:
        """Apply rule-based moderation"""
        text_lower = text.lower()
        warnings = []
        is_safe = True
        severity = "low"
        
        # Check harmful content
        for pattern in self.harmful_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                warnings.append("Potentially harmful content detected")
                is_safe = False
                severity = "high"
                break
        
        # Check inappropriate content
        for pattern in self.inappropriate_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                warnings.append("Inappropriate content detected")
                is_safe = False
                severity = "medium"
                break
        
        # Check for legal advice requests
        requires_disclaimer = False
        for pattern in self.legal_advice_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                warnings.append("Request may be seeking legal advice")
                requires_disclaimer = True
                severity = "medium"
                break
        
        return {
            "is_safe": is_safe,
            "warnings": warnings,
            "requires_disclaimer": requires_disclaimer,
            "severity": severity
        }
    
    async def _ai_based_moderation(self, text: str, content_type: str) -> Dict[str, Any]:
        """Use Groq for AI-based content moderation"""
        try:
            prompt = f"""
            Analyze the following {content_type} for safety and appropriateness in a legal assistant context:

            Text: "{text}"

            Evaluate for:
            1. Harmful or dangerous content
            2. Inappropriate requests
            3. Potential legal advice (if AI response)
            4. Compliance with content policies

            Respond with JSON only:
            {{
                "is_safe": true/false,
                "severity": "low/medium/high",
                "issues": ["list of specific issues"],
                "recommendation": "brief recommendation"
            }}
            """
            
            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                temperature=0.1,
                max_tokens=200
            )
            
            import json
            content = response.choices[0].message.content.strip()
            
            # Handle empty or non-JSON responses
            if not content:
                print("WARNING: Empty response from Groq moderation")
                return {"is_safe": True, "warnings": [], "severity": "low"}
            
            # Try to extract JSON from response
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # If not valid JSON, try to find JSON block
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    print(f"WARNING: Non-JSON response from Groq: {content[:100]}...")
                    return {"is_safe": True, "warnings": [], "severity": "low"}
            
            return {
                "is_safe": result.get("is_safe", True),
                "warnings": result.get("issues", []),
                "severity": result.get("severity", "low"),
                "ai_recommendation": result.get("recommendation", "")
            }
            
        except Exception as e:
            print(f"ERROR: AI moderation failed: {e}")
            return {"is_safe": True, "warnings": [], "severity": "low"}
    
    def _contains_legal_advice(self, text: str) -> bool:
        """Check if response contains legal advice"""
        advice_indicators = [
            "you should", "i recommend", "you must", "you need to",
            "file a lawsuit", "take legal action", "consult a lawyer",
            "in your case", "for your situation"
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in advice_indicators)
    
    def add_legal_disclaimer(self, response: str) -> str:
        """Add legal disclaimer to response"""
        disclaimer = "\n\n**Legal Disclaimer**: This information is for educational purposes only and does not constitute legal advice. Please consult with a qualified attorney for advice specific to your situation."
        return response + disclaimer
    
    def filter_harmful_content(self, text: str) -> str:
        """Filter out harmful content from text"""
        # Replace harmful patterns with safe alternatives
        filtered_text = text
        
        # Remove or replace harmful language
        harmful_replacements = {
            r'\b(kill|murder)\b': '[REMOVED]',
            r'\b(illegal|crime)\b': 'potentially problematic',
            r'\b(hate|racist)\b': '[INAPPROPRIATE]'
        }
        
        for pattern, replacement in harmful_replacements.items():
            filtered_text = re.sub(pattern, replacement, filtered_text, flags=re.IGNORECASE)
        
        return filtered_text

# Global moderation service instance
moderation_service = ModerationService()
