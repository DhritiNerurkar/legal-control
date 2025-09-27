"""
Real-time workflow status tracking for due diligence processing
"""
from typing import Dict, List, Optional
from datetime import datetime
import asyncio
from enum import Enum

class StepStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class WorkflowStep:
    def __init__(self, step_id: str, name: str, description: str, actions: List[str]):
        self.step_id = step_id
        self.name = name
        self.description = description
        self.actions = actions
        self.status = StepStatus.PENDING
        self.current_action = None
        self.current_action_index = 0
        self.start_time = None
        self.end_time = None
        self.details = []
        self.citations = []
        self.confidence = None
        self.error = None
        # New audit fields
        self.prompts_sent = []
        self.api_responses = []
        self.urls_accessed = []

    def start(self):
        self.status = StepStatus.IN_PROGRESS
        self.start_time = datetime.utcnow()
        if self.actions:
            self.current_action = self.actions[0]
            self.current_action_index = 0

    def next_action(self):
        if self.current_action_index < len(self.actions) - 1:
            self.current_action_index += 1
            self.current_action = self.actions[self.current_action_index]

    def complete(self, details: List[str] = None, citations: List[str] = None, confidence: float = None):
        self.status = StepStatus.COMPLETED
        self.end_time = datetime.utcnow()
        self.current_action = "Completed successfully"
        if details:
            self.details = details
        if citations:
            self.citations = citations
        if confidence:
            self.confidence = confidence

    def fail(self, error: str):
        self.status = StepStatus.FAILED
        self.end_time = datetime.utcnow()
        self.current_action = f"Failed: {error}"
        self.error = error

    def to_dict(self):
        return {
            "step_id": self.step_id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "current_action": self.current_action,
            "current_action_index": self.current_action_index,
            "total_actions": len(self.actions),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "details": self.details,
            "citations": self.citations,
            "confidence": self.confidence,
            "error": self.error,
            "progress_percentage": (self.current_action_index + 1) / len(self.actions) * 100 if self.actions else 0,
            # New audit fields
            "prompts_sent": self.prompts_sent,
            "api_responses": self.api_responses,
            "urls_accessed": self.urls_accessed
        }

class WorkflowTracker:
    _instances: Dict[str, 'WorkflowTracker'] = {}

    def __init__(self, check_id: str):
        self.check_id = check_id
        self.steps: List[WorkflowStep] = []
        self.current_step_index = 0
        self.overall_status = StepStatus.PENDING
        self.created_at = datetime.utcnow()
        self._initialize_steps()
        WorkflowTracker._instances[check_id] = self

    def _initialize_steps(self):
        """Initialize all 5-point due diligence steps with detailed actions"""
        steps_config = [
            {
                "step_id": "lei_lookup",
                "name": "1. LEI Database Lookup",
                "description": "Fetching entity data from GLEIF LEI database",
                "actions": [
                    "Connecting to GLEIF LEI API",
                    "Querying LEI database for entity information",
                    "Parsing LEI response data",
                    "Validating entity details",
                    "Extracting regulatory information"
                ]
            },
            {
                "step_id": "entity_classification",
                "name": "2. Entity Classification Analysis",
                "description": "AI analysis to classify entity type and regulatory status",
                "actions": [
                    "Preparing entity data for AI analysis",
                    "Sending classification prompt to Claude AI",
                    "Analyzing entity type indicators",
                    "Determining regulatory classification",
                    "Calculating classification confidence",
                    "Extracting limitations and recommendations"
                ]
            },
            {
                "step_id": "jurisdiction_analysis",
                "name": "3. Jurisdiction Analysis",
                "description": "Determining legal jurisdiction and governing law",
                "actions": [
                    "Analyzing incorporation jurisdiction",
                    "Identifying regulatory jurisdictions",
                    "Evaluating governing law implications",
                    "Assessing conflict of laws risks",
                    "Determining netting law applicability"
                ]
            },
            {
                "step_id": "authority_verification",
                "name": "4. Authority Verification",
                "description": "Verifying corporate authority to enter derivatives",
                "actions": [
                    "Analyzing corporate charter authority",
                    "Evaluating regulatory restrictions",
                    "Assessing investment mandate compliance",
                    "Reviewing board resolution requirements",
                    "Determining product-specific limitations"
                ]
            },
            {
                "step_id": "capacity_assessment",
                "name": "5. Legal Capacity Assessment",
                "description": "Evaluating legal capacity and ultra vires risks",
                "actions": [
                    "Analyzing corporate capacity under governing law",
                    "Evaluating ultra vires doctrine limitations",
                    "Assessing fiduciary duty constraints",
                    "Reviewing investment restrictions",
                    "Determining capacity limitations"
                ]
            },
            {
                "step_id": "legal_opinion_coverage",
                "name": "6. Legal Opinion Coverage",
                "description": "Analyzing netting enforceability and opinion coverage",
                "actions": [
                    "Reviewing available legal opinions",
                    "Analyzing netting enforceability coverage",
                    "Evaluating close-out rights protection",
                    "Assessing cross-border recognition",
                    "Identifying opinion gaps"
                ]
            },
            {
                "step_id": "risk_synthesis",
                "name": "7. Overall Risk Synthesis",
                "description": "Synthesizing findings into comprehensive risk assessment",
                "actions": [
                    "Consolidating all analysis results",
                    "Identifying key risk factors",
                    "Evaluating mitigating factors",
                    "Generating final recommendations",
                    "Calculating overall risk score"
                ]
            }
        ]

        for step_config in steps_config:
            step = WorkflowStep(
                step_id=step_config["step_id"],
                name=step_config["name"],
                description=step_config["description"],
                actions=step_config["actions"]
            )
            self.steps.append(step)

        # Start the first step immediately for UI display
        if self.steps:
            self.steps[0].start()
            self.current_step_index = 0
            self.overall_status = StepStatus.IN_PROGRESS

    @classmethod
    def get_tracker(cls, check_id: str) -> Optional['WorkflowTracker']:
        return cls._instances.get(check_id)

    @classmethod
    def create_tracker(cls, check_id: str) -> 'WorkflowTracker':
        return cls(check_id)

    def start_step(self, step_id: str):
        """Start a specific step and mark it as in progress"""
        for i, step in enumerate(self.steps):
            if step.step_id == step_id:
                step.start()
                self.current_step_index = i
                self.overall_status = StepStatus.IN_PROGRESS
                break

    def update_step_action(self, step_id: str, action_description: str = None):
        """Move to next action in current step or update with custom description"""
        for step in self.steps:
            if step.step_id == step_id and step.status == StepStatus.IN_PROGRESS:
                if action_description:
                    step.current_action = action_description
                else:
                    step.next_action()
                break

    def complete_step(self, step_id: str, details: List[str] = None, citations: List[str] = None, confidence: float = None):
        """Complete a step with results"""
        for step in self.steps:
            if step.step_id == step_id:
                step.complete(details, citations, confidence)
                break

    def fail_step(self, step_id: str, error: str):
        """Mark a step as failed"""
        for step in self.steps:
            if step.step_id == step_id:
                step.fail(error)
                self.overall_status = StepStatus.FAILED
                break

    def complete_workflow(self):
        """Mark entire workflow as completed"""
        self.overall_status = StepStatus.COMPLETED

    def add_prompt_to_step(self, step_id: str, prompt: str, response: str):
        """Add a prompt and response to a step's audit trail"""
        for step in self.steps:
            if step.step_id == step_id:
                step.prompts_sent.append(prompt)
                step.api_responses.append(response)
                break

    def add_url_to_step(self, step_id: str, url: str):
        """Add a URL to a step's audit trail"""
        for step in self.steps:
            if step.step_id == step_id:
                step.urls_accessed.append(url)
                break

    def get_status(self) -> Dict:
        """Get current workflow status for API response"""
        return {
            "check_id": self.check_id,
            "overall_status": self.overall_status.value,
            "current_step_index": self.current_step_index,
            "total_steps": len(self.steps),
            "steps": [step.to_dict() for step in self.steps],
            "created_at": self.created_at.isoformat(),
            "progress_percentage": (self.current_step_index / len(self.steps)) * 100 if self.overall_status == StepStatus.COMPLETED else ((self.current_step_index + 1) / len(self.steps)) * 100 if self.overall_status == StepStatus.IN_PROGRESS else 0
        }

    @classmethod
    def cleanup_tracker(cls, check_id: str):
        """Remove tracker when processing is complete"""
        if check_id in cls._instances:
            del cls._instances[check_id]