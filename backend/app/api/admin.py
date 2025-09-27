from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.database import get_db, DueDiligenceCheck
from app.services.workflow_tracker import WorkflowTracker

router = APIRouter()

@router.get("/logs/{check_id}")
async def get_admin_logs(
    check_id: str,
    db: Session = Depends(get_db)
):
    """Get admin logs (prompts and AI responses) for a due diligence check"""

    # Get the due diligence check
    db_check = db.query(DueDiligenceCheck).filter(
        DueDiligenceCheck.id == check_id
    ).first()

    if not db_check:
        raise HTTPException(status_code=404, detail="Due diligence check not found")

    # Get workflow tracker if it exists (for active processes)
    tracker = WorkflowTracker.get_tracker(check_id)

    admin_logs = []
    if tracker:
        # Process is active - get audit trail from tracker
        for step in tracker.steps:
            for i, prompt in enumerate(step.prompts_sent):
                response = step.api_responses[i] if i < len(step.api_responses) else "No response captured"
                admin_logs.append({
                    "step_name": step.name,
                    "step_id": step.step_id,
                    "prompt": prompt,
                    "response": response,
                    "timestamp": step.start_time.isoformat() if step.start_time else None,
                    "model": "claude-sonnet-4-20250514",
                    "prompt_length": len(prompt),
                    "response_length": len(response)
                })

    # Return admin logs from workflow tracker audit trail
    return {
        "check_id": check_id,
        "legal_name": db_check.legal_name,
        "lei_number": db_check.lei_number,
        "status": db_check.status,
        "admin_logs": admin_logs
    }