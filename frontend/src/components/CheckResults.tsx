import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  LinearProgress,
  Card,
  CardContent,
  Chip,
  Button,
  Alert,
  List,
  ListItem,
  ListItemText,
  CircularProgress,
  Tabs,
  Tab,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Download as DownloadIcon,
  ExpandMore as ExpandMoreIcon,
} from '@mui/icons-material';
import { DueDiligenceResponse, CheckStatus, CheckResult } from '../types/api';
import { dueDiligenceApi, reportsApi, adminApi } from '../services/api';
import WorkflowStatus from './WorkflowStatus';

interface ActionsSummaryProps {
  checkData: DueDiligenceResponse | null;
  onCommenceProcessing: () => void;
  isCommencing: boolean;
  onRestart?: () => void;
  workflowStarted: boolean;
}

const ActionsSummary: React.FC<ActionsSummaryProps> = ({ checkData, onCommenceProcessing, isCommencing, onRestart, workflowStarted }) => {
  const plannedActions = [
    {
      step: "1. LEI Database Lookup",
      description: "Fetch entity data from GLEIF LEI database",
      actions: [
        "Connect to GLEIF LEI API",
        "Query LEI database for entity information",
        "Parse LEI response data",
        "Validate entity details",
        "Extract regulatory information"
      ]
    },
    {
      step: "2. Entity Classification Analysis",
      description: "AI analysis to classify entity type and regulatory status",
      actions: [
        "Prepare entity data for AI analysis",
        "Send classification prompt to Claude AI",
        "Analyze entity type indicators",
        "Determine regulatory classification",
        "Calculate classification confidence",
        "Extract limitations and recommendations"
      ]
    },
    {
      step: "3. Jurisdiction Analysis",
      description: "Determine legal jurisdiction and governing law",
      actions: [
        "Analyze incorporation jurisdiction",
        "Identify regulatory jurisdictions",
        "Evaluate governing law implications",
        "Assess conflict of laws risks",
        "Determine netting law applicability"
      ]
    },
    {
      step: "4. Authority Verification",
      description: "Verify corporate authority to enter derivatives",
      actions: [
        "Analyze corporate charter authority",
        "Evaluate regulatory restrictions",
        "Assess investment mandate compliance",
        "Review board resolution requirements",
        "Determine product-specific limitations"
      ]
    },
    {
      step: "5. Legal Capacity Assessment",
      description: "Evaluate legal capacity and ultra vires risks",
      actions: [
        "Analyze corporate capacity under governing law",
        "Evaluate ultra vires doctrine limitations",
        "Assess fiduciary duty constraints",
        "Review investment restrictions",
        "Determine capacity limitations"
      ]
    },
    {
      step: "6. Legal Opinion Coverage",
      description: "Analyze netting enforceability and opinion coverage",
      actions: [
        "Review available legal opinions",
        "Analyze netting enforceability coverage",
        "Evaluate close-out rights protection",
        "Assess cross-border recognition",
        "Identify opinion gaps"
      ]
    },
    {
      step: "7. Overall Risk Synthesis",
      description: "Synthesize findings into comprehensive risk assessment",
      actions: [
        "Consolidate all analysis results",
        "Identify key risk factors",
        "Evaluate mitigating factors",
        "Generate final recommendations",
        "Calculate overall risk score"
      ]
    }
  ];

  return (
    <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        🤖 Due Diligence Actions Plan
      </Typography>

      {checkData && (
        <Box mb={3} p={2} bgcolor="info.50" borderRadius={1}>
          <Typography variant="subtitle2" gutterBottom>
            Entity Information:
          </Typography>
          <Typography variant="body2">
            <strong>Legal Name:</strong> {checkData.legal_name}
          </Typography>
          <Typography variant="body2">
            <strong>LEI:</strong> {checkData.lei_number}
          </Typography>
          <Typography variant="body2">
            <strong>Products:</strong> {checkData.products.join(', ')}
          </Typography>
        </Box>
      )}

      <Typography variant="body2" color="text.secondary" paragraph>
        The AI agent will perform the following actions in sequence:
      </Typography>

      <Box maxHeight={400} overflow="auto" mb={3}>
        {plannedActions.map((action, index) => (
          <Accordion key={index} elevation={1} sx={{ mb: 1 }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle2" color="primary">
                {action.step}
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography variant="body2" color="text.secondary" paragraph>
                {action.description}
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 'bold' }} gutterBottom>
                Planned Actions:
              </Typography>
              <List dense>
                {action.actions.map((step, stepIndex) => (
                  <ListItem key={stepIndex} sx={{ py: 0 }}>
                    <ListItemText
                      primary={`${stepIndex + 1}. ${step}`}
                      primaryTypographyProps={{ variant: 'body2' }}
                    />
                  </ListItem>
                ))}
              </List>
            </AccordionDetails>
          </Accordion>
        ))}
      </Box>

      <Box textAlign="center">
        {!workflowStarted ? (
          <Button
            variant="contained"
            size="medium"
            color="primary"
            onClick={onCommenceProcessing}
            disabled={isCommencing}
            sx={{ minWidth: 200 }}
          >
            {isCommencing ? '⏳ Starting...' : '🚀 Commence Due Diligence Check'}
          </Button>
        ) : (
          <Box display="flex" gap={2} justifyContent="center">
            <Button
              variant="contained"
              size="medium"
              color="primary"
              onClick={onCommenceProcessing}
              disabled={isCommencing}
              sx={{ minWidth: 200 }}
            >
              {isCommencing ? '⏳ Starting...' : '🔄 Run Check Again'}
            </Button>
            <Button
              variant="outlined"
              size="medium"
              color="secondary"
              onClick={onRestart}
              sx={{ minWidth: 150 }}
            >
              🏠 New Check
            </Button>
          </Box>
        )}
        <Typography variant="caption" display="block" color="text.secondary" sx={{ mt: 1 }}>
          {!workflowStarted
            ? 'Click to start the automated analysis process'
            : 'Run the same check again or start a completely new check'
          }
        </Typography>
      </Box>
    </Paper>
  );
};

interface CheckResultsProps {
  checkId: string;
}

const CheckResults: React.FC<CheckResultsProps> = ({ checkId }) => {
  const [checkData, setCheckData] = useState<DueDiligenceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloadingReport, setDownloadingReport] = useState(false);
  const [workflowStarted, setWorkflowStarted] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const [isCommencing, setIsCommencing] = useState(false);
  const [adminLogs, setAdminLogs] = useState<any>(null);
  const [loadingAdminLogs, setLoadingAdminLogs] = useState(false);

  useEffect(() => {
    const initializeCheck = async () => {
      await fetchCheckData();
    };

    initializeCheck();
  }, [checkId]);

  // Separate useEffect to handle status-based state updates
  useEffect(() => {
    if (checkData) {
      // Check if processing has already started - if so, enable workflow
      if (checkData.status === CheckStatus.IN_PROGRESS || checkData.status === CheckStatus.COMPLETED) {
        if (!workflowStarted) {
          setWorkflowStarted(true);
          // Only switch tabs if we're still on the first tab
          if (activeTab === 0) {
            setActiveTab(1); // Go to monitoring tab
          }
        }
      }
    }
  }, [checkData, workflowStarted, activeTab]);

  // Separate useEffect for polling
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    if (workflowStarted && activeTab === 1) {
      interval = setInterval(() => {
        if (checkData?.status === CheckStatus.IN_PROGRESS || checkData?.status === CheckStatus.PENDING) {
          fetchCheckData();
        }
      }, 2000); // Poll every 2 seconds
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [workflowStarted, activeTab, checkData?.status]);

  const fetchCheckData = async () => {
    try {
      const data = await dueDiligenceApi.getCheck(checkId);
      setCheckData(data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch check results');
    } finally {
      setLoading(false);
    }
  };

  const fetchAdminLogs = async () => {
    if (!checkData || loadingAdminLogs) return;

    setLoadingAdminLogs(true);
    try {
      const logs = await adminApi.getAdminLogs(checkId);
      setAdminLogs(logs);
    } catch (err: any) {
      console.error('Failed to fetch admin logs:', err);
      // Don't show error to user as this is admin functionality
    } finally {
      setLoadingAdminLogs(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'PASS':
        return <CheckCircleIcon color="success" />;
      case 'FAIL':
        return <ErrorIcon color="error" />;
      case 'REQUIRES_REVIEW':
        return <WarningIcon color="warning" />;
      default:
        return <WarningIcon color="action" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'PASS':
        return 'success';
      case 'FAIL':
        return 'error';
      case 'REQUIRES_REVIEW':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk?.toLowerCase()) {
      case 'low':
        return 'success';
      case 'medium':
        return 'warning';
      case 'high':
        return 'error';
      default:
        return 'default';
    }
  };

  const commenceProcessing = async () => {
    if (isCommencing) return; // Prevent double clicks

    // Check if processing is already running to prevent duplicate execution
    if (checkData?.status === CheckStatus.IN_PROGRESS) {
      setError('Processing is already in progress');
      return;
    }

    try {
      setIsCommencing(true);
      setError(''); // Clear any previous errors

      // Call API to start processing only if not already started
      if (checkData?.status === CheckStatus.PENDING || checkData?.status === CheckStatus.FAILED) {
        console.log(`Starting processing for check ${checkId}`);
        await dueDiligenceApi.startProcessing(checkId);
        console.log(`Processing started successfully for check ${checkId}`);
      } else {
        console.log(`Skipping API call - check ${checkId} status is ${checkData?.status}`);
      }

      setWorkflowStarted(true);
      setActiveTab(1); // Switch to monitoring tab

      // Force a data refresh after starting processing to ensure UI is in sync
      setTimeout(() => {
        fetchCheckData();
      }, 100);

    } catch (err: any) {
      console.error('Failed to start processing:', err);
      setError('Failed to start processing: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsCommencing(false);
    }
  };

  const restartCheck = () => {
    setWorkflowStarted(false);
    setActiveTab(0);
    setError(null);
  };

  const downloadReport = async (format: 'pdf' | 'html' | 'json') => {
    if (!checkData) return;

    setDownloadingReport(true);
    try {
      const blob = await reportsApi.generateReport({
        check_id: checkData.id,
        format,
      });

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `due_diligence_report_${checkData.id}.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError('Failed to download report');
    } finally {
      setDownloadingReport(false);
    }
  };

  const renderCheckResult = (title: string, result?: CheckResult) => {
    if (!result) {
      return (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="h6">{title}</Typography>
            <Typography color="text.secondary">Not yet processed</Typography>
          </CardContent>
        </Card>
      );
    }

    // Extract documentary evidence from enhanced prompts
    const primarySources = result.details?.primary_sources || [];
    const legalCitations = result.details?.legal_citations || [];
    const documentaryEvidence = result.details?.documentary_evidence_summary;
    const auditTrail = result.details?.audit_trail;
    const complianceFramework = result.details?.compliance_framework;

    return (
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
            <Typography variant="h6">{title}</Typography>
            <Box display="flex" alignItems="center" gap={1}>
              {getStatusIcon(result.status)}
              <Chip
                label={result.status}
                color={getStatusColor(result.status) as any}
                size="small"
              />
            </Box>
          </Box>

          <Typography variant="body2" paragraph>
            {result.summary}
          </Typography>

          <Box mb={2}>
            <Typography variant="body2" color="text.secondary">
              Confidence Score: {(result.confidence_score * 100).toFixed(1)}%
            </Typography>
            <LinearProgress
              variant="determinate"
              value={result.confidence_score * 100}
              sx={{ mt: 1 }}
            />
          </Box>

          {/* Documentary Evidence Section */}
          {(primarySources.length > 0 || legalCitations.length > 0 || documentaryEvidence) && (
            <Accordion sx={{ mb: 2 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="subtitle2" color="primary">
                  📄 Documentary Evidence & Legal Authority
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                {/* Primary Sources */}
                {primarySources.length > 0 && (
                  <Box mb={2}>
                    <Typography variant="body2" fontWeight="bold" gutterBottom>
                      Primary Sources:
                    </Typography>
                    {primarySources.map((source: any, index: number) => (
                      <Box key={index} sx={{ mb: 1, p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                        <Typography variant="body2" fontWeight="medium">
                          {source.source_type}: {source.citation || source.document_name}
                        </Typography>
                        {source.relevance && (
                          <Typography variant="caption" color="text.secondary">
                            {source.relevance}
                          </Typography>
                        )}
                        {source.authority && (
                          <Typography variant="caption" display="block" color="text.secondary">
                            Authority: {source.authority}
                          </Typography>
                        )}
                      </Box>
                    ))}
                  </Box>
                )}

                {/* Legal Citations */}
                {legalCitations.length > 0 && (
                  <Box mb={2}>
                    <Typography variant="body2" fontWeight="bold" gutterBottom>
                      Legal Citations:
                    </Typography>
                    {legalCitations.map((citation: any, index: number) => (
                      <Box key={index} sx={{ mb: 1, p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                        <Typography variant="body2" fontWeight="medium">
                          {citation.statute || citation.regulation}
                          {citation.section && ` - ${citation.section}`}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Authority: {citation.authority}
                        </Typography>
                        {citation.relevance && (
                          <Typography variant="caption" display="block" color="text.secondary">
                            {citation.relevance}
                          </Typography>
                        )}
                        {citation.url && (
                          <Typography variant="caption" display="block">
                            <a href={citation.url} target="_blank" rel="noopener noreferrer" style={{ color: '#1976d2' }}>
                              View Source →
                            </a>
                          </Typography>
                        )}
                      </Box>
                    ))}
                  </Box>
                )}

                {/* Evidence Summary */}
                {documentaryEvidence && (
                  <Box mb={2}>
                    <Typography variant="body2" fontWeight="bold" gutterBottom>
                      Evidence Strength Assessment:
                    </Typography>
                    <Box sx={{ p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                      <Typography variant="body2">
                        Sources Consulted: {documentaryEvidence.sources_consulted}
                      </Typography>
                      <Typography variant="body2">
                        Legal Authorities: {documentaryEvidence.legal_authorities_referenced || documentaryEvidence.official_documents_referenced}
                      </Typography>
                      <Typography variant="body2">
                        Evidence Strength: {documentaryEvidence.evidence_strength}
                      </Typography>
                      {documentaryEvidence.additional_documentation_required && (
                        <Box mt={1}>
                          <Typography variant="caption" color="warning.main" fontWeight="bold">
                            Additional Documentation Required:
                          </Typography>
                          {documentaryEvidence.additional_documentation_required.map((doc: string, idx: number) => (
                            <Typography key={idx} variant="caption" display="block" color="text.secondary">
                              • {doc}
                            </Typography>
                          ))}
                        </Box>
                      )}
                    </Box>
                  </Box>
                )}
              </AccordionDetails>
            </Accordion>
          )}

          {/* Audit Trail Section */}
          {auditTrail && (
            <Accordion sx={{ mb: 2 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="subtitle2" color="secondary">
                  🔍 Audit Trail & Methodology
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Box sx={{ p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                  {auditTrail.methodology && (
                    <Typography variant="body2" gutterBottom>
                      <strong>Methodology:</strong> {auditTrail.methodology}
                    </Typography>
                  )}
                  {auditTrail.data_sources_accessed && (
                    <Box mb={1}>
                      <Typography variant="body2" fontWeight="bold">Data Sources:</Typography>
                      {auditTrail.data_sources_accessed.map((source: string, idx: number) => (
                        <Typography key={idx} variant="caption" display="block" color="text.secondary">
                          • {source}
                        </Typography>
                      ))}
                    </Box>
                  )}
                  {auditTrail.limitations_identified && (
                    <Box>
                      <Typography variant="body2" fontWeight="bold" color="warning.main">Analysis Limitations:</Typography>
                      {auditTrail.limitations_identified.map((limitation: string, idx: number) => (
                        <Typography key={idx} variant="caption" display="block" color="text.secondary">
                          • {limitation}
                        </Typography>
                      ))}
                    </Box>
                  )}
                </Box>
              </AccordionDetails>
            </Accordion>
          )}

          {/* Compliance Framework Section */}
          {complianceFramework && (
            <Accordion sx={{ mb: 2 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="subtitle2" color="info.main">
                  ⚖️ Regulatory Compliance Framework
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Box sx={{ p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                  {complianceFramework.applicable_regulations && (
                    <Box mb={1}>
                      <Typography variant="body2" fontWeight="bold">Applicable Regulations:</Typography>
                      {complianceFramework.applicable_regulations.map((reg: string, idx: number) => (
                        <Typography key={idx} variant="caption" display="block" color="text.secondary">
                          • {reg}
                        </Typography>
                      ))}
                    </Box>
                  )}
                  {complianceFramework.regulatory_authorities && (
                    <Box mb={1}>
                      <Typography variant="body2" fontWeight="bold">Regulatory Authorities:</Typography>
                      {complianceFramework.regulatory_authorities.map((auth: string, idx: number) => (
                        <Typography key={idx} variant="caption" display="block" color="text.secondary">
                          • {auth}
                        </Typography>
                      ))}
                    </Box>
                  )}
                  {complianceFramework.documentation_requirements && (
                    <Box>
                      <Typography variant="body2" fontWeight="bold" color="primary.main">Documentation Requirements:</Typography>
                      {complianceFramework.documentation_requirements.map((req: string, idx: number) => (
                        <Typography key={idx} variant="caption" display="block" color="text.secondary">
                          • {req}
                        </Typography>
                      ))}
                    </Box>
                  )}
                </Box>
              </AccordionDetails>
            </Accordion>
          )}

          {result.limitations && result.limitations.length > 0 && (
            <Box mb={2}>
              <Typography variant="subtitle2" color="warning.main">
                Limitations:
              </Typography>
              <List dense>
                {result.limitations.map((limitation, index) => (
                  <ListItem key={index} sx={{ py: 0 }}>
                    <ListItemText primary={`• ${limitation}`} />
                  </ListItem>
                ))}
              </List>
            </Box>
          )}

          {result.recommendations && result.recommendations.length > 0 && (
            <Box>
              <Typography variant="subtitle2" color="primary.main">
                Recommendations:
              </Typography>
              <List dense>
                {result.recommendations.map((rec, index) => (
                  <ListItem key={index} sx={{ py: 0 }}>
                    <ListItemText primary={`• ${rec}`} />
                  </ListItem>
                ))}
              </List>
            </Box>
          )}
        </CardContent>
      </Card>
    );
  };

  if (loading && !checkData) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" action={
        <Button color="inherit" size="small" onClick={fetchCheckData}>
          Retry
        </Button>
      }>
        {error}
      </Alert>
    );
  }

  if (!checkData) {
    return <Alert severity="error">No check data found</Alert>;
  }


  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Tabs
        value={activeTab}
        onChange={handleTabChange}
        variant="fullWidth"
        sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}
      >
        <Tab label="📋 Agent Plan" />
        <Tab
          label="🔄 Live Monitoring"
          disabled={!workflowStarted && checkData?.status !== CheckStatus.IN_PROGRESS && checkData?.status !== CheckStatus.COMPLETED}
        />
        <Tab
          label="📊 Results"
          disabled={!workflowStarted && checkData?.status !== CheckStatus.COMPLETED}
        />
        <Tab
          label="🔧 Admin"
          disabled={!workflowStarted && checkData?.status !== CheckStatus.COMPLETED}
        />
      </Tabs>

      {/* Tab 0: Agent Plan */}
      {activeTab === 0 && (
        <Box>
          <ActionsSummary
            checkData={checkData}
            onCommenceProcessing={commenceProcessing}
            isCommencing={isCommencing}
            onRestart={restartCheck}
            workflowStarted={workflowStarted}
          />
        </Box>
      )}

      {/* Tab 1: Live Monitoring */}
      {activeTab === 1 && (
        <Box>
          {/* Simplified Entity Info Header */}
          <Box mb={3}>
            <Typography variant="h6" gutterBottom>
              🔄 Live Agent Monitoring
            </Typography>
            <Box display="flex" gap={2} flexWrap="wrap" alignItems="center">
              <Chip label={`Entity: ${checkData.legal_name}`} variant="outlined" />
              <Chip label={`LEI: ${checkData.lei_number}`} variant="outlined" />
              <Chip label={`Products: ${checkData.products.join(', ')}`} variant="outlined" />
              <Chip
                label={
                  checkData.status === CheckStatus.COMPLETED ? 'COMPLETED' :
                  checkData.status === CheckStatus.FAILED ? 'FAILED' :
                  'IN PROGRESS'
                }
                color={
                  checkData.status === CheckStatus.COMPLETED ? 'success' :
                  checkData.status === CheckStatus.FAILED ? 'error' :
                  'warning'
                }
                size="small"
              />
              {checkData.status === CheckStatus.COMPLETED && checkData.overall_risk_assessment && (
                <Chip
                  label={`Risk: ${checkData.overall_risk_assessment}`}
                  color={getRiskColor(checkData.overall_risk_assessment) as any}
                  size="small"
                />
              )}
            </Box>
          </Box>

          {/* Full Width Workflow Status */}
          {workflowStarted ? (
            <WorkflowStatus
              checkId={checkId}
              isActive={workflowStarted}
            />
          ) : (
            <Paper elevation={2} sx={{ p: 4, textAlign: 'center' }}>
              <Typography variant="h6" gutterBottom>
                🚀 Workflow Monitoring
              </Typography>
              <Typography variant="body2" color="text.secondary">
                The agent workflow will start here once you commence the due diligence check from the Agent Plan tab.
              </Typography>
            </Paper>
          )}

          {checkData.status === CheckStatus.FAILED && (
            <Alert severity="error" sx={{ mt: 2 }}>
              The due diligence check failed. Please try again or contact support.
            </Alert>
          )}
        </Box>
      )}

      {/* Tab 2: Results */}
      {activeTab === 2 && (
        <Box>
          {!workflowStarted ? (
            <Alert severity="info">
              Results will appear here once you start the due diligence check from the Agent Plan tab.
            </Alert>
          ) : checkData.status === CheckStatus.COMPLETED ? (
            <>
              <Typography variant="h6" gutterBottom>
                5-Point Check Results
              </Typography>

              {renderCheckResult('1. Entity Classification', checkData.entity_classification)}
              {renderCheckResult('2. Jurisdiction', checkData.jurisdiction)}
              {renderCheckResult('3. Authority', checkData.authority)}
              {renderCheckResult('4. Capacity', checkData.capacity)}
              {renderCheckResult('5. Legal Opinion', checkData.legal_opinion)}

              {checkData.overall_recommendations && checkData.overall_recommendations.length > 0 && (
                <Card sx={{ mt: 3 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom color="primary">
                      Overall Recommendations
                    </Typography>
                    <List>
                      {checkData.overall_recommendations.map((rec, index) => (
                        <ListItem key={index}>
                          <ListItemText primary={`${index + 1}. ${rec}`} />
                        </ListItem>
                      ))}
                    </List>
                  </CardContent>
                </Card>
              )}

              <Paper elevation={1} sx={{ p: 3, mt: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Download Report
                </Typography>
                <Box display="flex" gap={2} flexWrap="wrap">
                  <Button
                    variant="contained"
                    startIcon={<DownloadIcon />}
                    onClick={() => downloadReport('pdf')}
                    disabled={downloadingReport}
                  >
                    PDF Report
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<DownloadIcon />}
                    onClick={() => downloadReport('html')}
                    disabled={downloadingReport}
                  >
                    HTML Report
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<DownloadIcon />}
                    onClick={() => downloadReport('json')}
                    disabled={downloadingReport}
                  >
                    JSON Report
                  </Button>
                </Box>
              </Paper>
            </>
          ) : (
            <Alert severity="info">
              Results will appear here once the due diligence check is completed.
            </Alert>
          )}
        </Box>
      )}

      {/* Tab 3: Admin */}
      {activeTab === 3 && (
        <Box>
          <Typography variant="h6" gutterBottom>
            🔧 Admin: Prompt & Response Logs
          </Typography>

          {!adminLogs && (
            <Box display="flex" alignItems="center" gap={2}>
              <Button
                variant="contained"
                onClick={() => {
                  if (!loadingAdminLogs) {
                    fetchAdminLogs();
                  }
                }}
                disabled={loadingAdminLogs}
                startIcon={loadingAdminLogs ? <CircularProgress size={16} /> : null}
              >
                {loadingAdminLogs ? 'Loading...' : 'Load Admin Logs'}
              </Button>
              <Typography variant="body2" color="text.secondary">
                View AI prompts and responses for debugging and inference
              </Typography>
            </Box>
          )}

          {adminLogs && adminLogs.admin_logs && adminLogs.admin_logs.length > 0 ? (
            <Box>
              <Typography variant="body2" color="text.secondary" paragraph>
                Entity: {adminLogs.legal_name} ({adminLogs.lei_number}) - Status: {adminLogs.status?.toUpperCase()}
              </Typography>

              {adminLogs.admin_logs.map((log: any, index: number) => (
                <Accordion key={index} sx={{ mb: 2 }}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Box display="flex" alignItems="center" gap={2}>
                      <Typography variant="h6" color="primary">
                        {log.step_name}
                      </Typography>
                      <Chip
                        label={`${log.prompt_length || 0} chars → ${log.response_length || 0} chars`}
                        size="small"
                        variant="outlined"
                      />
                      {log.timestamp && (
                        <Typography variant="caption" color="text.secondary">
                          {new Date(log.timestamp).toLocaleString()}
                        </Typography>
                      )}
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box>
                      {/* AI Prompt Section */}
                      <Accordion sx={{ mb: 2 }}>
                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                          <Typography variant="subtitle1" color="secondary">
                            📝 AI Prompt ({log.prompt_length || 0} characters)
                          </Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                          <Paper
                            variant="outlined"
                            sx={{
                              p: 2,
                              backgroundColor: '#f8f9fa',
                              maxHeight: '400px',
                              overflow: 'auto',
                            }}
                          >
                            <Typography
                              variant="body2"
                              component="pre"
                              sx={{
                                whiteSpace: 'pre-wrap',
                                fontSize: '12px',
                                fontFamily: 'monospace',
                              }}
                            >
                              {log.prompt || 'No prompt available'}
                            </Typography>
                          </Paper>
                        </AccordionDetails>
                      </Accordion>

                      {/* AI Response Section */}
                      {log.response && (
                        <Accordion>
                          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                            <Typography variant="subtitle1" color="success.main">
                              🤖 AI Response ({log.response_length || 0} characters)
                            </Typography>
                          </AccordionSummary>
                          <AccordionDetails>
                            <Paper
                              variant="outlined"
                              sx={{
                                p: 2,
                                backgroundColor: '#f0fff0',
                                maxHeight: '600px',
                                overflow: 'auto',
                              }}
                            >
                              <Typography
                                variant="body2"
                                component="pre"
                                sx={{
                                  whiteSpace: 'pre-wrap',
                                  fontSize: '12px',
                                  fontFamily: 'monospace',
                                }}
                              >
                                {log.response}
                              </Typography>
                            </Paper>
                          </AccordionDetails>
                        </Accordion>
                      )}

                      {/* Error Section */}
                      {log.error && (
                        <Alert severity="error" sx={{ mt: 2 }}>
                          <Typography variant="body2">
                            <strong>Error:</strong> {log.error}
                          </Typography>
                        </Alert>
                      )}

                      {/* Model Info */}
                      <Box sx={{ mt: 2, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                        <Chip label={`Model: ${log.model || 'Unknown'}`} size="small" />
                        {log.max_tokens && (
                          <Chip label={`Max Tokens: ${log.max_tokens}`} size="small" />
                        )}
                        {log.temperature !== undefined && (
                          <Chip label={`Temperature: ${log.temperature}`} size="small" />
                        )}
                      </Box>
                    </Box>
                  </AccordionDetails>
                </Accordion>
              ))}
            </Box>
          ) : adminLogs && adminLogs.admin_logs && adminLogs.admin_logs.length === 0 ? (
            <Alert severity="info">
              No admin logs available for this due diligence check.
            </Alert>
          ) : null}
        </Box>
      )}
    </Box>
  );
};

// Fixed UI issues
export default CheckResults;