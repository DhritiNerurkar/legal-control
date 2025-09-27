from fastapi import APIRouter, HTTPException, Depends, Response
from sqlalchemy.orm import Session
from app.models.database import get_db, DueDiligenceCheck
from app.models.schemas import ReportRequest
from app.services.report_generator import ReportGenerator

router = APIRouter()

@router.post("/generate")
async def generate_report(
    request: ReportRequest,
    db: Session = Depends(get_db)
):
    """Generate a due diligence report"""

    # Get the due diligence check
    db_check = db.query(DueDiligenceCheck).filter(
        DueDiligenceCheck.id == request.check_id
    ).first()

    if not db_check:
        raise HTTPException(status_code=404, detail="Due diligence check not found")

    if db_check.status != "completed":
        raise HTTPException(status_code=400, detail="Due diligence check not completed")

    # Generate report
    report_generator = ReportGenerator()

    if request.format.lower() == "pdf":
        report_content = await report_generator.generate_pdf_report(db_check)
        media_type = "application/pdf"
        filename = f"due_diligence_report_{request.check_id}.pdf"
    elif request.format.lower() == "html":
        report_content = await report_generator.generate_html_report(db_check)
        media_type = "text/html"
        filename = f"due_diligence_report_{request.check_id}.html"
    elif request.format.lower() == "json":
        report_content = await report_generator.generate_json_report(db_check)
        media_type = "application/json"
        filename = f"due_diligence_report_{request.check_id}.json"
    else:
        raise HTTPException(status_code=400, detail="Unsupported report format")

    return Response(
        content=report_content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )