export interface DueDiligenceRequest {
  legal_name: string;
  lei_number: string;
  products: ProductType[];
}

export enum ProductType {
  ISDA = 'ISDA',
  CSA = 'CSA',
  MRA = 'MRA',
  GMRA = 'GMRA',
  MSFTA = 'MSFTA',
  SECURITIES_LENDING = 'Securities Lending'
}

export enum CheckStatus {
  PENDING = 'pending',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

export interface CheckResult {
  check_type: string;
  status: 'PASS' | 'FAIL' | 'REQUIRES_REVIEW' | 'NOT_APPLICABLE';
  confidence_score: number;
  summary: string;
  details: Record<string, any>;
  evidence_sources: string[];
  limitations: string[];
  recommendations: string[];
}

export interface DueDiligenceResponse {
  id: string;
  lei_number: string;
  legal_name: string;
  products: ProductType[];
  status: CheckStatus;

  // 5-point check results
  entity_classification?: CheckResult;
  jurisdiction?: CheckResult;
  authority?: CheckResult;
  capacity?: CheckResult;
  legal_opinion?: CheckResult;

  overall_risk_assessment?: string;
  overall_recommendations: string[];

  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export interface EntityInfo {
  lei_number: string;
  legal_name: string;
  entity_type: string;
  jurisdiction: string;
  incorporation_date?: string;
  regulatory_status?: string;
  website?: string;
  business_description?: string;
  authorized_products: string[];
  capacity_limitations: string[];
  regulatory_body?: string;
}

export interface ReportRequest {
  check_id: string;
  format: 'pdf' | 'html' | 'json';
}