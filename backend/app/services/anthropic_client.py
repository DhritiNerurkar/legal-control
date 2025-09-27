import anthropic
from app.core.config import settings
from typing import List, Dict, Any
import json
import re
from datetime import datetime

class AnthropicClient:
    def __init__(self):
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"Initializing AnthropicClient with model: {settings.ANTHROPIC_MODEL}")

        if not settings.ANTHROPIC_API_KEY:
            logger.error("ANTHROPIC_API_KEY environment variable not set")
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        logger.info(f"ANTHROPIC_API_KEY found: {settings.ANTHROPIC_API_KEY[:20]}...")

        self.client = anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY
        )

        logger.info("AnthropicClient initialized successfully")

    def extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """Extract JSON from AI response that might contain extra text"""
        try:
            # First try direct parsing
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON within the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

            # If no valid JSON found, return structured error
            return {
                "error": "Failed to parse JSON from AI response",
                "raw_response": response,
                "structured": False
            }

    async def generate(self, prompt: str, max_tokens: int = 12000, temperature: float = 0.3) -> str:
        """Generate response using Claude with enhanced parameters for detailed analysis"""
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"Making API call to Anthropic model: {settings.ANTHROPIC_MODEL}")
        logger.info(f"Prompt length: {len(prompt)} chars, max_tokens: {max_tokens}")

        try:
            response = self.client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=max_tokens,
                temperature=temperature,  # Lower temperature for more consistent, factual responses
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                # Enable additional reasoning and research-like behavior
                system="You are a legal and regulatory expert with extensive knowledge of financial entity regulations, SEC filings, corporate structures, and derivatives law. When analyzing entities, draw upon your comprehensive knowledge of regulatory databases, common corporate structures, and legal frameworks. Provide detailed analysis with specific regulatory citations and multiple verification approaches."
            )

            logger.info(f"API call successful, response length: {len(response.content[0].text)} chars")
            return response.content[0].text

        except Exception as e:
            logger.error(f"Anthropic API error: {str(e)}")
            raise Exception(f"Anthropic API error: {str(e)}")

    async def generate_with_logs(self, prompt: str, step_name: str, max_tokens: int = 12000, temperature: float = 0.3) -> tuple[str, dict]:
        """Generate response and return both response and log data for admin purposes"""
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"Making API call for step '{step_name}' to Anthropic model: {settings.ANTHROPIC_MODEL}")

        try:
            response = self.client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                system="You are a legal and regulatory expert with extensive knowledge of financial entity regulations, SEC filings, corporate structures, and derivatives law. When analyzing entities, draw upon your comprehensive knowledge of regulatory databases, common corporate structures, and legal frameworks. Provide detailed analysis with specific regulatory citations and multiple verification approaches."
            )

            response_text = response.content[0].text

            # Create admin log entry
            admin_log = {
                "step_name": step_name,
                "prompt": prompt,
                "response": response_text,
                "model": settings.ANTHROPIC_MODEL,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "prompt_length": len(prompt),
                "response_length": len(response_text),
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"API call successful for step '{step_name}', response length: {len(response_text)} chars")
            return response_text, admin_log

        except Exception as e:
            logger.error(f"Anthropic API error for step '{step_name}': {str(e)}")
            # Create error log entry
            admin_log = {
                "step_name": step_name,
                "prompt": prompt,
                "response": None,
                "error": str(e),
                "model": settings.ANTHROPIC_MODEL,
                "timestamp": datetime.now().isoformat()
            }
            raise Exception(f"Anthropic API error: {str(e)}")

    async def analyze_document(self, document_text: str, analysis_type: str) -> Dict[str, Any]:
        """Analyze a document for specific information"""

        prompt = f"""
        Analyze the following legal document for {analysis_type}:

        Document:
        {document_text}

        Extract relevant information and provide structured analysis in JSON format.
        Focus on:
        - Authority provisions
        - Capacity limitations
        - Product restrictions
        - Regulatory constraints
        - Governing law clauses
        """

        response = await self.generate(prompt)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"analysis": response, "structured": False}

    async def classify_entity(self, entity_info: Dict[str, Any]) -> Dict[str, Any]:
        """Classify entity type based on available information"""

        prompt = f"""
        Based on the following entity information, classify the entity type:

        {json.dumps(entity_info, indent=2)}

        Classify into one of these categories:
        - Commercial Bank
        - Investment Bank
        - Hedge Fund
        - Asset Manager
        - Pension Fund
        - Insurance Company
        - Sovereign Wealth Fund
        - Corporation
        - Other (specify)

        Provide confidence score and reasoning in JSON format:
        {{
            "entity_type": "...",
            "confidence_score": 0.0-1.0,
            "reasoning": "...",
            "key_indicators": [...],
            "alternative_classifications": [...]
        }}
        """

        response = await self.generate(prompt)
        return json.loads(response)

    async def assess_jurisdiction_risks(self, jurisdiction: str, entity_type: str, products: List[str]) -> Dict[str, Any]:
        """Assess jurisdiction-specific risks for derivative transactions"""

        prompt = f"""
        Assess the legal risks for derivative transactions in the following context:

        Jurisdiction: {jurisdiction}
        Entity Type: {entity_type}
        Products: {products}

        Consider:
        1. Netting enforceability
        2. Close-out provisions
        3. Insolvency laws
        4. Regulatory restrictions
        5. Foreign exchange controls

        Provide risk assessment in JSON format:
        {{
            "overall_risk": "LOW/MEDIUM/HIGH",
            "netting_risk": "...",
            "insolvency_risk": "...",
            "regulatory_risk": "...",
            "fx_controls_risk": "...",
            "key_concerns": [...],
            "mitigating_factors": [...],
            "recommendations": [...]
        }}
        """

        response = await self.generate(prompt)
        return json.loads(response)