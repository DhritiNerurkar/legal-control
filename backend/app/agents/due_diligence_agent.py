import json
from datetime import datetime
from typing import Dict, List, Any
from langgraph.graph import StateGraph
from langchain.schema import BaseMessage
from pydantic import BaseModel
from app.core.config import settings
from app.services.anthropic_client import AnthropicClient
from app.services.external_sources import ExternalSourcesClient
from app.services.document_processor import DocumentProcessor
from app.models.database import SessionLocal, DueDiligenceCheck
from app.models.schemas import CheckResult, CheckStatus

class DueDiligenceState(BaseModel):
    check_id: str
    lei_number: str
    legal_name: str
    products: List[str]

    # 5-point check states
    entity_classification: Dict[str, Any] = {}
    jurisdiction: Dict[str, Any] = {}
    authority: Dict[str, Any] = {}
    capacity: Dict[str, Any] = {}
    legal_opinion: Dict[str, Any] = {}

    # Evidence and sources
    sources_checked: List[str] = []
    evidence_documents: List[Dict] = []

    # Final results
    overall_assessment: str = ""
    recommendations: List[str] = []
    errors: List[str] = []

    # Admin logs for debugging
    admin_logs: List[Dict] = []

class DueDiligenceAgent:
    def __init__(self):
        self.anthropic_client = AnthropicClient()
        self.external_sources = ExternalSourcesClient()
        self.document_processor = DocumentProcessor()
        self.workflow = self._create_workflow()

    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow for due diligence checks"""

        workflow = StateGraph(DueDiligenceState)

        # Define nodes
        workflow.add_node("initialize", self._initialize_check)
        workflow.add_node("entity_classification", self._check_entity_classification)
        workflow.add_node("jurisdiction_check", self._check_jurisdiction)
        workflow.add_node("authority_check", self._check_authority)
        workflow.add_node("capacity_check", self._check_capacity)
        workflow.add_node("legal_opinion_check", self._check_legal_opinion)
        workflow.add_node("synthesize_results", self._synthesize_results)
        workflow.add_node("finalize", self._finalize_check)

        # Define edges
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "entity_classification")
        workflow.add_edge("entity_classification", "jurisdiction_check")
        workflow.add_edge("jurisdiction_check", "authority_check")
        workflow.add_edge("authority_check", "capacity_check")
        workflow.add_edge("capacity_check", "legal_opinion_check")
        workflow.add_edge("legal_opinion_check", "synthesize_results")
        workflow.add_edge("synthesize_results", "finalize")

        return workflow.compile()

    async def process_check(self, check_id: str, request_data: Dict):
        """Process a due diligence check"""

        # Update status to in progress
        db = SessionLocal()
        try:
            db_check = db.query(DueDiligenceCheck).filter(
                DueDiligenceCheck.id == check_id
            ).first()
            if db_check:
                db_check.status = CheckStatus.IN_PROGRESS.value
                db.commit()
        finally:
            db.close()

        # Initialize state
        initial_state = DueDiligenceState(
            check_id=check_id,
            lei_number=request_data["lei_number"],
            legal_name=request_data["legal_name"],
            products=request_data["products"]
        )

        try:
            # Run the workflow
            result = await self.workflow.ainvoke(initial_state)

            # Save results to database
            await self._save_results(result)

        except Exception as e:
            # Handle errors
            db = SessionLocal()
            try:
                db_check = db.query(DueDiligenceCheck).filter(
                    DueDiligenceCheck.id == check_id
                ).first()
                if db_check:
                    db_check.status = CheckStatus.FAILED.value
                    db_check.updated_at = datetime.utcnow()
                    db.commit()
            finally:
                db.close()
            raise e

    async def _initialize_check(self, state: DueDiligenceState) -> DueDiligenceState:
        """Initialize the due diligence check"""

        # Validate LEI number format
        if not self._validate_lei(state.lei_number):
            state.errors.append("Invalid LEI number format")
            return state

        # Load any existing organizational documents
        documents = await self.document_processor.get_entity_documents(state.lei_number)
        state.evidence_documents.extend(documents)

        return state

    async def _check_entity_classification(self, state: DueDiligenceState) -> DueDiligenceState:
        """Check 1: Entity Classification"""

        try:
            # Gather information from external sources
            lei_info = await self.external_sources.get_lei_data(state.lei_number)
            regulatory_info = await self.external_sources.get_regulatory_data(
                state.legal_name, state.lei_number
            )

            # Use Claude to analyze and classify the entity
            classification_prompt = f"""
            Analyze the following entity information and classify the entity type:

            Legal Name: {state.legal_name}
            LEI Number: {state.lei_number}
            LEI Data: {json.dumps(lei_info, indent=2)}
            Regulatory Data: {json.dumps(regulatory_info, indent=2)}

            Classify this entity into one of these categories:
            - Commercial Bank
            - Investment Bank
            - Hedge Fund
            - Asset Manager
            - Pension Fund
            - Insurance Company
            - Sovereign Wealth Fund
            - Corporation

            Provide your analysis in JSON format:
            {{
                "entity_type": "...",
                "confidence_score": 0.0-1.0,
                "reasoning": "...",
                "evidence_sources": [...],
                "limitations": [...]
            }}
            """

            response, admin_log = await self.anthropic_client.generate_with_logs(
                classification_prompt, "entity_classification"
            )
            state.admin_logs.append(admin_log)
            classification_result = json.loads(response)

            # Create check result
            state.entity_classification = {
                "check_type": "entity_classification",
                "status": "PASS" if classification_result["confidence_score"] > 0.7 else "REQUIRES_REVIEW",
                "confidence_score": classification_result["confidence_score"],
                "summary": f"Entity classified as {classification_result['entity_type']}",
                "details": classification_result,
                "evidence_sources": state.sources_checked + ["LEI Database", "Regulatory Filings"],
                "limitations": classification_result.get("limitations", []),
                "recommendations": []
            }

        except Exception as e:
            state.entity_classification = {
                "check_type": "entity_classification",
                "status": "FAIL",
                "confidence_score": 0.0,
                "summary": f"Entity classification failed: {str(e)}",
                "details": {"error": str(e)},
                "evidence_sources": [],
                "limitations": ["Unable to access external data sources"],
                "recommendations": ["Manual review required"]
            }

        return state

    async def _check_jurisdiction(self, state: DueDiligenceState) -> DueDiligenceState:
        """Check 2: Jurisdiction"""

        try:
            # Get incorporation information
            incorporation_info = await self.external_sources.get_incorporation_data(
                state.legal_name, state.lei_number
            )

            jurisdiction_prompt = f"""
            Analyze the jurisdiction information for this entity:

            Legal Name: {state.legal_name}
            LEI Number: {state.lei_number}
            Incorporation Data: {json.dumps(incorporation_info, indent=2)}

            Determine:
            1. The jurisdiction where the entity is incorporated
            2. The governing law for the entity
            3. Any regulatory jurisdictions that apply
            4. Potential conflicts of laws issues

            Provide analysis in JSON format:
            {{
                "primary_jurisdiction": "...",
                "incorporation_jurisdiction": "...",
                "regulatory_jurisdictions": [...],
                "governing_law": "...",
                "confidence_score": 0.0-1.0,
                "conflicts_of_law": [...],
                "reasoning": "..."
            }}
            """

            response, admin_log = await self.anthropic_client.generate_with_logs(
                jurisdiction_prompt, "jurisdiction_check"
            )
            state.admin_logs.append(admin_log)
            jurisdiction_result = json.loads(response)

            state.jurisdiction = {
                "check_type": "jurisdiction",
                "status": "PASS",
                "confidence_score": jurisdiction_result["confidence_score"],
                "summary": f"Entity incorporated in {jurisdiction_result['primary_jurisdiction']}",
                "details": jurisdiction_result,
                "evidence_sources": ["Corporate Registry", "LEI Database"],
                "limitations": jurisdiction_result.get("conflicts_of_law", []),
                "recommendations": []
            }

        except Exception as e:
            state.jurisdiction = {
                "check_type": "jurisdiction",
                "status": "FAIL",
                "confidence_score": 0.0,
                "summary": f"Jurisdiction check failed: {str(e)}",
                "details": {"error": str(e)},
                "evidence_sources": [],
                "limitations": ["Unable to verify incorporation details"],
                "recommendations": ["Manual verification required"]
            }

        return state

    async def _check_authority(self, state: DueDiligenceState) -> DueDiligenceState:
        """Check 3: Authority"""

        try:
            # Analyze organizational documents for authority provisions
            authority_analysis = await self.document_processor.analyze_authority(
                state.lei_number, state.products
            )

            authority_prompt = f"""
            Analyze the authority of this entity to enter into derivative contracts:

            Entity: {state.legal_name}
            Products: {state.products}
            Document Analysis: {json.dumps(authority_analysis, indent=2)}
            Entity Classification: {state.entity_classification.get('details', {})}

            Determine if the entity has authority to enter into the requested products.
            Consider:
            1. Corporate charter/constitutional documents
            2. Regulatory authorizations
            3. Board resolutions
            4. Investment management agreements

            Provide analysis in JSON format:
            {{
                "has_authority": true/false,
                "authority_source": "...",
                "authorized_products": [...],
                "limitations": [...],
                "confidence_score": 0.0-1.0,
                "reasoning": "..."
            }}
            """

            response, admin_log = await self.anthropic_client.generate_with_logs(
                authority_prompt, "authority_check"
            )
            state.admin_logs.append(admin_log)
            authority_result = json.loads(response)

            status = "PASS" if authority_result["has_authority"] else "FAIL"

            state.authority = {
                "check_type": "authority",
                "status": status,
                "confidence_score": authority_result["confidence_score"],
                "summary": f"Entity {'has' if authority_result['has_authority'] else 'lacks'} authority for requested products",
                "details": authority_result,
                "evidence_sources": ["Organizational Documents", "Regulatory Filings"],
                "limitations": authority_result.get("limitations", []),
                "recommendations": [] if authority_result["has_authority"] else ["Obtain board resolution or regulatory approval"]
            }

        except Exception as e:
            state.authority = {
                "check_type": "authority",
                "status": "REQUIRES_REVIEW",
                "confidence_score": 0.0,
                "summary": f"Authority check inconclusive: {str(e)}",
                "details": {"error": str(e)},
                "evidence_sources": [],
                "limitations": ["Insufficient documentation"],
                "recommendations": ["Manual review of organizational documents required"]
            }

        return state

    async def _check_capacity(self, state: DueDiligenceState) -> DueDiligenceState:
        """Check 4: Capacity"""

        try:
            capacity_prompt = f"""
            Analyze the capacity of this entity to enter into derivative contracts:

            Entity: {state.legal_name}
            Entity Type: {state.entity_classification.get('details', {}).get('entity_type', 'Unknown')}
            Jurisdiction: {state.jurisdiction.get('details', {}).get('primary_jurisdiction', 'Unknown')}
            Products: {state.products}

            Consider legal capacity factors:
            1. Corporate capacity under governing law
            2. Regulatory constraints
            3. Investment restrictions
            4. Ultra vires concerns
            5. Fiduciary duties

            Provide analysis in JSON format:
            {{
                "has_capacity": true/false,
                "capacity_limitations": [...],
                "regulatory_constraints": [...],
                "investment_restrictions": [...],
                "confidence_score": 0.0-1.0,
                "reasoning": "..."
            }}
            """

            response, admin_log = await self.anthropic_client.generate_with_logs(
                capacity_prompt, "capacity_check"
            )
            state.admin_logs.append(admin_log)
            capacity_result = json.loads(response)

            status = "PASS" if capacity_result["has_capacity"] else "FAIL"

            state.capacity = {
                "check_type": "capacity",
                "status": status,
                "confidence_score": capacity_result["confidence_score"],
                "summary": f"Entity {'has' if capacity_result['has_capacity'] else 'lacks'} capacity for requested products",
                "details": capacity_result,
                "evidence_sources": ["Legal Analysis", "Regulatory Review"],
                "limitations": capacity_result.get("capacity_limitations", []),
                "recommendations": [] if capacity_result["has_capacity"] else ["Seek legal opinion on capacity"]
            }

        except Exception as e:
            state.capacity = {
                "check_type": "capacity",
                "status": "REQUIRES_REVIEW",
                "confidence_score": 0.0,
                "summary": f"Capacity check failed: {str(e)}",
                "details": {"error": str(e)},
                "evidence_sources": [],
                "limitations": ["Unable to determine capacity"],
                "recommendations": ["Legal opinion required"]
            }

        return state

    async def _check_legal_opinion(self, state: DueDiligenceState) -> DueDiligenceState:
        """Check 5: Legal Opinion"""

        try:
            entity_type = state.entity_classification.get('details', {}).get('entity_type', 'Unknown')
            jurisdiction = state.jurisdiction.get('details', {}).get('primary_jurisdiction', 'Unknown')

            # Check internal legal opinion database
            opinion_coverage = await self.external_sources.get_legal_opinion_coverage(
                entity_type, jurisdiction, state.products
            )

            opinion_prompt = f"""
            Analyze legal opinion coverage for netting and close-out rights:

            Entity Type: {entity_type}
            Jurisdiction: {jurisdiction}
            Products: {state.products}
            Opinion Coverage: {json.dumps(opinion_coverage, indent=2)}

            Determine if there is adequate legal opinion coverage for:
            1. Netting enforceability
            2. Close-out netting rights
            3. Set-off rights

            Provide analysis in JSON format:
            {{
                "opinion_available": true/false,
                "netting_covered": true/false,
                "closeout_covered": true/false,
                "opinion_gaps": [...],
                "confidence_score": 0.0-1.0,
                "reasoning": "..."
            }}
            """

            response, admin_log = await self.anthropic_client.generate_with_logs(
                opinion_prompt, "legal_opinion_check"
            )
            state.admin_logs.append(admin_log)
            opinion_result = json.loads(response)

            status = "PASS" if opinion_result["opinion_available"] and opinion_result["netting_covered"] else "REQUIRES_REVIEW"

            state.legal_opinion = {
                "check_type": "legal_opinion",
                "status": status,
                "confidence_score": opinion_result["confidence_score"],
                "summary": f"Legal opinion {'provides adequate' if status == 'PASS' else 'lacks adequate'} coverage",
                "details": opinion_result,
                "evidence_sources": ["Legal Opinion Database", "Law Firm Opinions"],
                "limitations": opinion_result.get("opinion_gaps", []),
                "recommendations": [] if status == "PASS" else ["Obtain additional legal opinion"]
            }

        except Exception as e:
            state.legal_opinion = {
                "check_type": "legal_opinion",
                "status": "REQUIRES_REVIEW",
                "confidence_score": 0.0,
                "summary": f"Legal opinion check failed: {str(e)}",
                "details": {"error": str(e)},
                "evidence_sources": [],
                "limitations": ["Unable to verify opinion coverage"],
                "recommendations": ["Manual review of legal opinions required"]
            }

        return state

    async def _synthesize_results(self, state: DueDiligenceState) -> DueDiligenceState:
        """Synthesize all check results into overall assessment"""

        synthesis_prompt = f"""
        Synthesize the following due diligence check results:

        Entity Classification: {json.dumps(state.entity_classification, indent=2)}
        Jurisdiction: {json.dumps(state.jurisdiction, indent=2)}
        Authority: {json.dumps(state.authority, indent=2)}
        Capacity: {json.dumps(state.capacity, indent=2)}
        Legal Opinion: {json.dumps(state.legal_opinion, indent=2)}

        Provide overall risk assessment and recommendations:
        {{
            "overall_risk": "LOW/MEDIUM/HIGH",
            "key_findings": [...],
            "critical_issues": [...],
            "recommendations": [...],
            "approval_recommendation": "APPROVE/CONDITIONAL_APPROVAL/REJECT"
        }}
        """

        try:
            response, admin_log = await self.anthropic_client.generate_with_logs(
                synthesis_prompt, "synthesize_results"
            )
            state.admin_logs.append(admin_log)
            synthesis_result = json.loads(response)

            state.overall_assessment = synthesis_result["overall_risk"]
            state.recommendations = synthesis_result["recommendations"]

        except Exception as e:
            state.overall_assessment = "HIGH"
            state.recommendations = ["Manual review required due to synthesis error"]
            state.errors.append(f"Synthesis error: {str(e)}")

        return state

    async def _finalize_check(self, state: DueDiligenceState) -> DueDiligenceState:
        """Finalize the due diligence check"""

        # This node marks the completion of the workflow
        # The actual database saving is handled in save_results
        return state

    async def _save_results(self, state: DueDiligenceState):
        """Save results to database"""

        db = SessionLocal()
        try:
            db_check = db.query(DueDiligenceCheck).filter(
                DueDiligenceCheck.id == state.check_id
            ).first()

            if db_check:
                db_check.status = CheckStatus.COMPLETED.value
                db_check.entity_classification_result = state.entity_classification
                db_check.jurisdiction_result = state.jurisdiction
                db_check.authority_result = state.authority
                db_check.capacity_result = state.capacity
                db_check.legal_opinion_result = state.legal_opinion
                db_check.sources_checked = state.sources_checked
                db_check.evidence_documents = state.evidence_documents
                db_check.risk_assessment = state.overall_assessment
                db_check.recommendations = '\n'.join(state.recommendations)
                db_check.admin_logs = state.admin_logs
                db_check.updated_at = datetime.utcnow()
                db_check.completed_at = datetime.utcnow()

                db.commit()

        finally:
            db.close()

    def _validate_lei(self, lei: str) -> bool:
        """Validate LEI number format"""
        return len(lei) == 20 and lei.isalnum()