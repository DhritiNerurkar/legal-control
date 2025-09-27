import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  LinearProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert,
  AlertTitle,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
  Search as SearchIcon,
  Gavel as GavelIcon,
  Business as BusinessIcon,
  Security as SecurityIcon,
  Description as DescriptionIcon,
  ExpandMore as ExpandMoreIcon,
  Info as InfoIcon,
  Stop as StopIcon,
  Timer as TimerIcon,
  FindInPage as AuditIcon,
  Link as LinkIcon,
} from '@mui/icons-material';

interface WorkflowStep {
  id: string;
  name: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  current_action?: string;
  current_action_index?: number;
  total_actions?: number;
  progress_percentage?: number;
  details?: string[];
  citations?: string[];
  confidence?: number;
  startTime?: string;
  endTime?: string;
  icon: React.ReactNode;
}

interface WorkflowStatusProps {
  checkId: string;
  isActive: boolean;
}

const WorkflowStatus: React.FC<WorkflowStatusProps> = ({
  checkId,
  isActive
}) => {
  const [auditDialogOpen, setAuditDialogOpen] = useState(false);
  const [dataSourceInfo, setDataSourceInfo] = useState<{
    usedRealAPIs: boolean;
    usedSyntheticData: boolean;
    apiDetails: string[];
  }>({
    usedRealAPIs: false,
    usedSyntheticData: false,
    apiDetails: []
  });

  const [steps, setSteps] = useState<WorkflowStep[]>([
    {
      id: 'lei_lookup',
      name: '1. LEI Database Lookup',
      description: 'Fetching entity data from GLEIF LEI database',
      status: 'pending',
      icon: <SearchIcon />,
    },
    {
      id: 'entity_classification',
      name: '2. Entity Classification Analysis',
      description: 'AI analysis of entity type and regulatory status',
      status: 'pending',
      icon: <BusinessIcon />,
    },
    {
      id: 'jurisdiction_analysis',
      name: '3. Jurisdiction Analysis',
      description: 'Legal jurisdiction and governing law determination',
      status: 'pending',
      icon: <GavelIcon />,
    },
    {
      id: 'authority_verification',
      name: '4. Authority Verification',
      description: 'Corporate authority to enter derivative transactions',
      status: 'pending',
      icon: <SecurityIcon />,
    },
    {
      id: 'capacity_assessment',
      name: '5. Legal Capacity Assessment',
      description: 'Legal capacity and ultra vires analysis',
      status: 'pending',
      icon: <SecurityIcon />,
    },
    {
      id: 'legal_opinion_coverage',
      name: '6. Legal Opinion Coverage',
      description: 'Netting enforceability and opinion coverage analysis',
      status: 'pending',
      icon: <DescriptionIcon />,
    },
    {
      id: 'risk_synthesis',
      name: '7. Overall Risk Synthesis',
      description: 'Comprehensive risk assessment and recommendations',
      status: 'pending',
      icon: <GavelIcon />,
    },
  ]);

  const [activeStep, setActiveStep] = useState(0);

  // Poll backend for real workflow status
  useEffect(() => {
    console.log('WorkflowStatus effect triggered:', { isActive, checkId });

    if (!isActive) {
      console.log('WorkflowStatus: Not active, skipping polling');
      return;
    }

    const pollWorkflow = async () => {
      try {
        console.log(`Polling workflow status for check ID: ${checkId}`);
        const response = await fetch(`http://localhost:8000/api/v1/due-diligence/${checkId}/workflow-status`);
        console.log('Workflow status response:', response.status, response.ok);

        if (response.ok) {
          const workflowData = await response.json();
          console.log('Workflow data received:', workflowData);
          console.log('First step audit data:', workflowData.steps?.[0]?.prompts_sent, workflowData.steps?.[0]?.api_responses);

          // Convert backend data to component format with icons
          const iconMap = [
            <SearchIcon />,
            <BusinessIcon />,
            <GavelIcon />,
            <SecurityIcon />,
            <SecurityIcon />,
            <DescriptionIcon />,
            <GavelIcon />
          ];

          const convertedSteps = workflowData.steps.map((step: any, stepIndex: number) => ({
            id: step.step_id || step.id,
            name: step.name,
            description: step.description,
            status: step.status,
            current_action: step.current_action,
            current_action_index: step.current_action_index,
            total_actions: step.total_actions,
            progress_percentage: step.progress_percentage,
            details: step.details || [],
            citations: step.citations || [],
            confidence: step.confidence,
            startTime: step.start_time || step.startTime,
            endTime: step.end_time || step.endTime,
            icon: iconMap[stepIndex] || <BusinessIcon />,
            // Add missing audit fields
            prompts_sent: step.prompts_sent || [],
            api_responses: step.api_responses || [],
            urls_accessed: step.urls_accessed || []
          }));

          console.log('Setting steps:', convertedSteps);
          setSteps(convertedSteps);
          setActiveStep(workflowData.current_step_index || 0);

          // Analyze data sources to provide transparency
          const hasRealAPIs = convertedSteps.some((step: any) =>
            step.citations?.some((citation: string) =>
              citation.includes('GLEIF') || citation.includes('Claude') || citation.includes('Anthropic')
            )
          );

          const hasSyntheticData = convertedSteps.some((step: any) =>
            step.citations?.some((citation: string) =>
              citation.includes('Synthetic') || citation.includes('fallback')
            )
          );

          const apiDetails = [];
          if (hasRealAPIs) {
            if (convertedSteps.some((step: any) => step.citations?.some((c: string) => c.includes('GLEIF')))) {
              apiDetails.push('GLEIF LEI Database');
            }
            if (convertedSteps.some((step: any) => step.citations?.some((c: string) => c.includes('Claude') || c.includes('Anthropic')))) {
              apiDetails.push('Anthropic Claude AI');
            }
          }

          setDataSourceInfo({
            usedRealAPIs: hasRealAPIs,
            usedSyntheticData: hasSyntheticData,
            apiDetails
          });
        } else {
          console.error('Failed to fetch workflow status:', response.status, response.statusText);
        }
      } catch (error) {
        console.error('Failed to fetch workflow status:', error);
      }
    };

    // Initial fetch
    pollWorkflow();

    // Poll every 2 seconds for real-time updates
    const interval = setInterval(pollWorkflow, 2000);

    return () => {
      console.log('Cleaning up workflow polling interval');
      clearInterval(interval);
    };
  }, [checkId, isActive]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon color="success" />;
      case 'failed':
        return <ErrorIcon color="error" />;
      case 'in_progress':
        return <ScheduleIcon color="primary" />;
      default:
        return <ScheduleIcon color="disabled" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'in_progress':
        return 'primary';
      default:
        return 'default';
    }
  };

  // Always show workflow if component is mounted - no longer wait for backend data
  // This ensures immediate display when user starts due diligence

  return (
    <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">
          🤖 AI Agent Workflow Progress - Check ID: {checkId}
        </Typography>
        <Button
          variant="outlined"
          size="small"
          startIcon={<AuditIcon />}
          onClick={() => setAuditDialogOpen(true)}
          disabled={steps.every(step => step.status === 'pending')}
        >
          Audit Trail
        </Button>
      </Box>


      {steps.length === 0 ? (
        <Typography color="text.secondary">Loading workflow status...</Typography>
      ) : (
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Showing live progress for {steps.length} workflow steps
        </Typography>
      )}

      {/* Data Source Transparency Note */}
      <Accordion sx={{ mb: 2 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box display="flex" alignItems="center" gap={1}>
            <InfoIcon color="primary" />
            <Typography variant="body2" color="primary">
              Data Sources & AI Usage Transparency
            </Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Alert
            severity={dataSourceInfo.usedRealAPIs ? "success" : "warning"}
            sx={{ mb: 2 }}
          >
            <AlertTitle>
              {dataSourceInfo.usedRealAPIs ? "Real APIs Used" : "Synthetic Data Used"}
            </AlertTitle>
            {dataSourceInfo.usedRealAPIs ? (
              <>
                This analysis used real external APIs and AI services:
                <List dense>
                  {dataSourceInfo.apiDetails.map((api, index) => (
                    <ListItem key={index}>
                      <ListItemText primary={`✓ ${api}`} />
                    </ListItem>
                  ))}
                </List>
              </>
            ) : (
              "This analysis used synthetic/fallback data due to API unavailability. Results are for demonstration purposes only."
            )}
          </Alert>
          {dataSourceInfo.usedSyntheticData && (
            <Alert severity="info">
              <AlertTitle>Fallback Data Used</AlertTitle>
              Some steps used synthetic data when external APIs were unavailable.
              Check individual step citations for specific data sources.
            </Alert>
          )}
        </AccordionDetails>
      </Accordion>

      <Stepper activeStep={activeStep} orientation="vertical">
        {steps.map((step) => (
          <Step key={step.id}>
            <StepLabel
              StepIconComponent={() => getStatusIcon(step.status)}
              optional={
                step.status === 'in_progress' && (
                  <LinearProgress sx={{ mt: 1 }} />
                )
              }
            >
              <Box>
                <Box display="flex" alignItems="center" gap={1} mb={1}>
                  {step.icon}
                  <Typography variant="subtitle1">{step.name}</Typography>
                </Box>
                <Box display="flex" gap={1} flexWrap="wrap">
                  <Chip
                    label={step.status.replace('_', ' ').toUpperCase()}
                    color={getStatusColor(step.status) as any}
                    size="small"
                  />
                  {step.confidence && (
                    <Chip
                      label={`${(step.confidence * 100).toFixed(1)}% confidence`}
                      variant="outlined"
                      size="small"
                    />
                  )}
                </Box>
              </Box>
            </StepLabel>
            <StepContent>
              <Typography color="text.secondary" paragraph>
                {step.description}
              </Typography>

              {/* Live Current Action Display */}
              {step.status === 'in_progress' && step.current_action && (
                <Box sx={{ mb: 2, p: 2, bgcolor: 'primary.50', borderRadius: 1 }}>
                  <Typography variant="body2" color="primary" fontWeight="bold" gutterBottom>
                    🤖 Agent Action:
                  </Typography>
                  <Typography variant="body2" color="primary">
                    {step.current_action}
                  </Typography>
                  {step.progress_percentage && (
                    <LinearProgress
                      variant="determinate"
                      value={step.progress_percentage}
                      sx={{ mt: 1 }}
                    />
                  )}
                  {step.current_action_index !== undefined && step.total_actions && (
                    <Typography variant="caption" color="text.secondary">
                      Step {step.current_action_index + 1} of {step.total_actions}
                    </Typography>
                  )}
                </Box>
              )}

              {step.details && step.details.length > 0 && (
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="body2">Analysis Details</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <List dense>
                      {step.details.map((detail, idx) => (
                        <ListItem key={idx}>
                          <ListItemText primary={`• ${detail}`} />
                        </ListItem>
                      ))}
                    </List>
                  </AccordionDetails>
                </Accordion>
              )}

              {step.citations && step.citations.length > 0 && (
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="body2">Data Sources & Citations</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <List dense>
                      {step.citations.map((citation, idx) => (
                        <ListItem key={idx}>
                          <ListItemText
                            primary={`• ${citation}`}
                            primaryTypographyProps={{
                              variant: 'body2',
                              color: 'primary'
                            }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </AccordionDetails>
                </Accordion>
              )}

              {/* LLM Prompts and Responses for Debugging */}
              {(step as any).prompts_sent && (step as any).prompts_sent.length > 0 && (
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="body2" color="secondary">
                      🤖 LLM Debug: Prompts & Responses ({(step as any).prompts_sent.length})
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    {(step as any).prompts_sent.map((prompt: string, idx: number) => (
                      <Accordion key={idx} sx={{ mb: 1 }}>
                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                          <Typography variant="caption" color="secondary">
                            Prompt #{idx + 1} - Click to expand raw LLM interaction
                          </Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                          <Box sx={{ mb: 2 }}>
                            <Typography variant="caption" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                              📤 Prompt Sent to LLM:
                            </Typography>
                            <Paper elevation={1} sx={{ p: 2, mt: 1, bgcolor: 'info.50', maxHeight: 300, overflow: 'auto' }}>
                              <Typography
                                variant="body2"
                                sx={{
                                  fontFamily: 'monospace',
                                  fontSize: '0.75rem',
                                  whiteSpace: 'pre-wrap',
                                  wordBreak: 'break-word'
                                }}
                              >
                                {prompt}
                              </Typography>
                            </Paper>
                          </Box>
                          <Box>
                            <Typography variant="caption" sx={{ fontWeight: 'bold', color: 'success.main' }}>
                              📥 Raw LLM Response:
                            </Typography>
                            <Paper elevation={1} sx={{ p: 2, mt: 1, bgcolor: 'success.50', maxHeight: 300, overflow: 'auto' }}>
                              <Typography
                                variant="body2"
                                sx={{
                                  fontFamily: 'monospace',
                                  fontSize: '0.75rem',
                                  whiteSpace: 'pre-wrap',
                                  wordBreak: 'break-word'
                                }}
                              >
                                {(step as any).api_responses && (step as any).api_responses[idx]
                                  ? (step as any).api_responses[idx]
                                  : 'No response recorded for this prompt'
                                }
                              </Typography>
                            </Paper>
                          </Box>
                        </AccordionDetails>
                      </Accordion>
                    ))}
                  </AccordionDetails>
                </Accordion>
              )}

              {step.startTime && (
                <Typography variant="caption" color="text.secondary">
                  Started: {new Date(step.startTime).toLocaleString()}
                  {step.endTime && (
                    <> • Completed: {new Date(step.endTime).toLocaleString()}</>
                  )}
                </Typography>
              )}
            </StepContent>
          </Step>
        ))}
      </Stepper>

      {/* Audit Trail Dialog */}
      <Dialog
        open={auditDialogOpen}
        onClose={() => setAuditDialogOpen(false)}
        maxWidth="lg"
        fullWidth
        scroll="paper"
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <AuditIcon />
            <Typography variant="h6">
              Detailed Audit Trail - Agent Activity Report
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          {steps.filter(step => step.status !== 'pending').map((step) => (
            <Box key={step.id} mb={3}>
              <Typography variant="h6" color="primary" gutterBottom>
                {step.name}
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Status: {step.status.toUpperCase()} |
                {step.confidence && ` Confidence: ${(step.confidence * 100).toFixed(1)}%`}
              </Typography>

              {/* Detailed Actions Performed */}
              <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
                🤖 Agent Actions Performed:
              </Typography>
              <Paper elevation={1} sx={{ p: 2, mb: 2, bgcolor: 'grey.50' }}>
                {step.current_action ? (
                  <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                    Current Action: {step.current_action}
                  </Typography>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No specific actions recorded for this step.
                  </Typography>
                )}
              </Paper>

              {/* AI Prompts and Responses */}
              {(step as any).prompts_sent && (step as any).prompts_sent.length > 0 && (
                <>
                  <Typography variant="subtitle2" gutterBottom>
                    💭 AI Prompts Sent & Responses:
                  </Typography>
                  {(step as any).prompts_sent.map((prompt: string, idx: number) => (
                    <Paper key={idx} elevation={1} sx={{ p: 2, mb: 2, bgcolor: 'info.50' }}>
                      <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                        Prompt #{idx + 1}:
                      </Typography>
                      <Box sx={{ maxHeight: 200, overflow: 'auto', mb: 2 }}>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.75rem', whiteSpace: 'pre-wrap' }}>
                          {prompt}
                        </Typography>
                      </Box>
                      <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                        AI Response:
                      </Typography>
                      <Box sx={{ maxHeight: 200, overflow: 'auto' }}>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.75rem', whiteSpace: 'pre-wrap' }}>
                          {(step as any).api_responses && (step as any).api_responses[idx] ? (step as any).api_responses[idx] : 'No response recorded'}
                        </Typography>
                      </Box>
                    </Paper>
                  ))}
                </>
              )}

              {/* URLs and Data Sources Accessed */}
              <Typography variant="subtitle2" gutterBottom>
                🌐 URLs & Data Sources Accessed:
              </Typography>
              <Paper elevation={1} sx={{ p: 2, mb: 2, bgcolor: 'primary.50' }}>
                {step.citations && step.citations.length > 0 ? (
                  step.citations.map((citation, idx) => (
                    <Box key={idx} mb={1}>
                      <Box display="flex" alignItems="center" gap={1}>
                        <LinkIcon fontSize="small" color="primary" />
                        <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                          {citation.includes('http') ? (
                            <a href={citation} target="_blank" rel="noopener noreferrer" style={{ color: 'inherit' }}>
                              {citation}
                            </a>
                          ) : (
                            citation
                          )}
                        </Typography>
                      </Box>
                    </Box>
                  ))
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No specific URLs or data sources recorded.
                  </Typography>
                )}
              </Paper>

              {/* Discoveries and Results */}
              {step.details && step.details.length > 0 && (
                <>
                  <Typography variant="subtitle2" gutterBottom>
                    🔍 Discoveries & Results:
                  </Typography>
                  <Paper elevation={1} sx={{ p: 2, mb: 2, bgcolor: 'success.50' }}>
                    {step.details.map((detail, idx) => (
                      <Typography key={idx} variant="body2" paragraph>
                        • {detail}
                      </Typography>
                    ))}
                  </Paper>
                </>
              )}

              {/* Timestamps */}
              {step.startTime && (
                <Typography variant="caption" color="text.secondary">
                  ⏱️ Started: {new Date(step.startTime).toLocaleString()}
                  {step.endTime && (
                    <> | Completed: {new Date(step.endTime).toLocaleString()}</>
                  )}
                </Typography>
              )}

              <Divider sx={{ mt: 2 }} />
            </Box>
          ))}

          {steps.every(step => step.status === 'pending') && (
            <Typography variant="body1" color="text.secondary" textAlign="center" py={4}>
              No audit data available yet. Steps will appear here as processing begins.
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAuditDialogOpen(false)}>
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
};

export default WorkflowStatus;