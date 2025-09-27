from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class EntityType(str, Enum):
    COMMERCIAL_BANK = "Commercial Bank"
    INVESTMENT_BANK = "Investment Bank"
    HEDGE_FUND = "Hedge Fund"
    ASSET_MANAGER = "Asset Manager"
    PENSION_FUND = "Pension Fund"
    INSURANCE_COMPANY = "Insurance Company"
    SOVEREIGN_WEALTH_FUND = "Sovereign Wealth Fund"
    CORPORATION = "Corporation"

class ProductType(str, Enum):
    ISDA = "ISDA"
    CSA = "CSA"
    MRA = "MRA"
    GMRA = "GMRA"
    MSFTA = "MSFTA"
    SECURITIES_LENDING = "Securities Lending"

class CheckStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class DueDiligenceRequest(BaseModel):
    legal_name: str = Field(..., description="Legal name of the entity")
    lei_number: str = Field(..., description="LEI number of the entity")
    products: List[ProductType] = Field(..., description="Products for due diligence check")

class EvidenceSource(BaseModel):
    source: str
    url: Optional[str] = None
    accessed: str
    model: Optional[str] = None
    referenced_check: Optional[str] = None
    description: Optional[str] = None

class CheckResult(BaseModel):
    check_type: str
    status: str  # PASS, FAIL, REQUIRES_REVIEW, NOT_APPLICABLE
    confidence_score: float = Field(ge=0.0, le=1.0)
    summary: str
    details: Dict[str, Any]
    evidence_sources: List[EvidenceSource]
    limitations: List[str] = []
    recommendations: List[str] = []

class DueDiligenceResponse(BaseModel):
    id: str
    lei_number: str
    legal_name: str
    products: List[ProductType]
    status: CheckStatus

    # 5-point check results
    entity_classification: Optional[CheckResult] = None
    jurisdiction: Optional[CheckResult] = None
    authority: Optional[CheckResult] = None
    capacity: Optional[CheckResult] = None
    legal_opinion: Optional[CheckResult] = None

    overall_risk_assessment: Optional[str] = None
    overall_recommendations: List[str] = []

    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

class EntityInfo(BaseModel):
    lei_number: str
    legal_name: str
    entity_type: str
    jurisdiction: str
    incorporation_date: Optional[datetime] = None
    regulatory_status: Optional[str] = None
    website: Optional[str] = None
    business_description: Optional[str] = None
    authorized_products: List[str] = []
    capacity_limitations: List[str] = []
    regulatory_body: Optional[str] = None

class LegalOpinionInfo(BaseModel):
    id: str
    entity_type: str
    jurisdiction: str
    product: str
    opinion_available: bool
    opinion_provider: Optional[str] = None
    opinion_date: Optional[datetime] = None
    netting_enforceability: Optional[str] = None
    close_out_netting: Optional[str] = None
    opinion_summary: Optional[str] = None
    limitations: List[str] = []

class ReportRequest(BaseModel):
    check_id: str
    format: str = "pdf"  # pdf, html, json