import json
from datetime import datetime
from typing import Dict, Any
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from jinja2 import Template
import io

class ReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()

    def _create_custom_styles(self):
        """Create custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            textColor=colors.darkblue
        ))

        self.styles.add(ParagraphStyle(
            name='CheckResult',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=12,
            leftIndent=20
        ))

    async def generate_pdf_report(self, due_diligence_check) -> bytes:
        """Generate PDF report"""

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []

        # Title
        title = Paragraph("Legal Entity Due Diligence Report", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 12))

        # Entity Information
        entity_info = [
            ["Entity Name:", due_diligence_check.legal_name],
            ["LEI Number:", due_diligence_check.lei_number],
            ["Products:", ", ".join(due_diligence_check.products)],
            ["Check Date:", due_diligence_check.created_at.strftime("%Y-%m-%d %H:%M")],
            ["Status:", due_diligence_check.status.upper()],
            ["Risk Assessment:", due_diligence_check.risk_assessment or "N/A"]
        ]

        entity_table = Table(entity_info, colWidths=[2*inch, 4*inch])
        entity_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(entity_table)
        story.append(Spacer(1, 20))

        # 5-Point Check Results
        story.append(Paragraph("Due Diligence Check Results", self.styles['Heading2']))
        story.append(Spacer(1, 12))

        checks = [
            ("Entity Classification", due_diligence_check.entity_classification_result),
            ("Jurisdiction", due_diligence_check.jurisdiction_result),
            ("Authority", due_diligence_check.authority_result),
            ("Capacity", due_diligence_check.capacity_result),
            ("Legal Opinion", due_diligence_check.legal_opinion_result)
        ]

        for check_name, check_result in checks:
            if check_result:
                story.append(Paragraph(f"<b>{check_name}</b>", self.styles['Heading3']))

                result_data = [
                    ["Status:", check_result.get("status", "N/A")],
                    ["Confidence Score:", f"{check_result.get('confidence_score', 0):.2f}"],
                    ["Summary:", check_result.get("summary", "N/A")]
                ]

                result_table = Table(result_data, colWidths=[1.5*inch, 4.5*inch])
                result_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey)
                ]))

                story.append(result_table)

                # Add detailed analysis sections
                details = check_result.get("details", {})

                # Documentary Evidence & Legal Authority
                primary_sources = details.get("primary_sources", [])
                legal_citations = details.get("legal_citations", [])
                documentary_evidence = details.get("documentary_evidence_summary")

                if primary_sources or legal_citations or documentary_evidence:
                    story.append(Paragraph("<b>Documentary Evidence & Legal Authority:</b>", self.styles['Normal']))

                    # Primary Sources
                    if primary_sources:
                        story.append(Paragraph("<b>Primary Sources:</b>", self.styles['CheckResult']))
                        for source in primary_sources:
                            source_text = f"• {source.get('source_type', 'Unknown')}: {source.get('citation', source.get('document_name', 'N/A'))}"
                            if source.get('relevance'):
                                source_text += f" - {source.get('relevance')}"
                            if source.get('authority'):
                                source_text += f" (Authority: {source.get('authority')})"
                            if source.get('url'):
                                source_text += f" <link href='{source.get('url')}' color='blue'>[View Source]</link>"
                            story.append(Paragraph(source_text, self.styles['CheckResult']))

                    # Legal Citations
                    if legal_citations:
                        story.append(Paragraph("<b>Legal Citations:</b>", self.styles['CheckResult']))
                        for citation in legal_citations:
                            citation_text = f"• {citation.get('statute', citation.get('regulation', 'N/A'))}"
                            if citation.get('section'):
                                citation_text += f" - {citation.get('section')}"
                            citation_text += f" (Authority: {citation.get('authority', 'N/A')})"
                            if citation.get('relevance'):
                                citation_text += f" - {citation.get('relevance')}"
                            if citation.get('url'):
                                citation_text += f" <link href='{citation.get('url')}' color='blue'>[View Source]</link>"
                            story.append(Paragraph(citation_text, self.styles['CheckResult']))

                    # Evidence Summary
                    if documentary_evidence:
                        story.append(Paragraph("<b>Evidence Strength Assessment:</b>", self.styles['CheckResult']))
                        story.append(Paragraph(f"• Sources Consulted: {documentary_evidence.get('sources_consulted', 'N/A')}", self.styles['CheckResult']))
                        story.append(Paragraph(f"• Legal Authorities: {documentary_evidence.get('legal_authorities_referenced', documentary_evidence.get('official_documents_referenced', 'N/A'))}", self.styles['CheckResult']))
                        story.append(Paragraph(f"• Evidence Strength: {documentary_evidence.get('evidence_strength', 'N/A')}", self.styles['CheckResult']))

                        additional_docs = documentary_evidence.get('additional_documentation_required', [])
                        if additional_docs:
                            story.append(Paragraph("<b>Additional Documentation Required:</b>", self.styles['CheckResult']))
                            for additional_doc in additional_docs:
                                story.append(Paragraph(f"• {additional_doc}", self.styles['CheckResult']))

                # Audit Trail & Methodology
                audit_trail = details.get("audit_trail")
                if audit_trail:
                    story.append(Paragraph("<b>Audit Trail & Methodology:</b>", self.styles['Normal']))
                    if audit_trail.get('methodology'):
                        story.append(Paragraph(f"Methodology: {audit_trail.get('methodology')}", self.styles['CheckResult']))

                    data_sources = audit_trail.get('data_sources_accessed', [])
                    if data_sources:
                        story.append(Paragraph("Data Sources:", self.styles['CheckResult']))
                        for source in data_sources:
                            story.append(Paragraph(f"• {source}", self.styles['CheckResult']))

                    limitations = audit_trail.get('limitations_identified', [])
                    if limitations:
                        story.append(Paragraph("Analysis Limitations:", self.styles['CheckResult']))
                        for limitation in limitations:
                            story.append(Paragraph(f"• {limitation}", self.styles['CheckResult']))

                # Regulatory Compliance Framework
                compliance_framework = details.get("compliance_framework")
                if compliance_framework:
                    story.append(Paragraph("<b>Regulatory Compliance Framework:</b>", self.styles['Normal']))

                    applicable_regs = compliance_framework.get('applicable_regulations', [])
                    if applicable_regs:
                        story.append(Paragraph("Applicable Regulations:", self.styles['CheckResult']))
                        for reg in applicable_regs:
                            story.append(Paragraph(f"• {reg}", self.styles['CheckResult']))

                    reg_authorities = compliance_framework.get('regulatory_authorities', [])
                    if reg_authorities:
                        story.append(Paragraph("Regulatory Authorities:", self.styles['CheckResult']))
                        for auth in reg_authorities:
                            story.append(Paragraph(f"• {auth}", self.styles['CheckResult']))

                    doc_requirements = compliance_framework.get('documentation_requirements', [])
                    if doc_requirements:
                        story.append(Paragraph("Documentation Requirements:", self.styles['CheckResult']))
                        for req in doc_requirements:
                            story.append(Paragraph(f"• {req}", self.styles['CheckResult']))

                # Add limitations if any
                limitations = check_result.get("limitations", [])
                if limitations:
                    story.append(Paragraph("<b>Limitations:</b>", self.styles['Normal']))
                    for limitation in limitations:
                        story.append(Paragraph(f"• {limitation}", self.styles['CheckResult']))

                # Add recommendations if any
                recommendations = check_result.get("recommendations", [])
                if recommendations:
                    story.append(Paragraph("<b>Recommendations:</b>", self.styles['Normal']))
                    for recommendation in recommendations:
                        story.append(Paragraph(f"• {recommendation}", self.styles['CheckResult']))

                story.append(Spacer(1, 15))

        # Overall Recommendations
        if due_diligence_check.recommendations:
            story.append(Paragraph("Overall Recommendations", self.styles['Heading2']))
            story.append(Spacer(1, 12))

            recommendations = due_diligence_check.recommendations.split('\n')
            for rec in recommendations:
                if rec.strip():
                    story.append(Paragraph(f"• {rec.strip()}", self.styles['CheckResult']))

        # Footer
        story.append(Spacer(1, 30))
        footer_text = f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by Legal Entity Due Diligence System"
        story.append(Paragraph(footer_text, self.styles['Normal']))

        doc.build(story)
        pdf = buffer.getvalue()
        buffer.close()

        return pdf

    async def generate_html_report(self, due_diligence_check) -> str:
        """Generate HTML report"""

        template_str = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Legal Entity Due Diligence Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .header { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
                .entity-info { background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; }
                .check-result { margin: 20px 0; padding: 15px; border-left: 4px solid #3498db; }
                .status-pass { border-left-color: #27ae60; }
                .status-fail { border-left-color: #e74c3c; }
                .status-review { border-left-color: #f39c12; }
                .confidence-score { font-weight: bold; }
                .recommendations { background-color: #fff3cd; padding: 15px; border-radius: 5px; }
                table { width: 100%; border-collapse: collapse; margin: 10px 0; }
                th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background-color: #f2f2f2; }
                .footer { margin-top: 40px; font-size: 12px; color: #666; }
                .source-link {
                    color: #1976d2 !important;
                    font-weight: bold;
                    text-decoration: none;
                    background-color: #e3f2fd;
                    padding: 4px 8px;
                    border-radius: 4px;
                    display: inline-block;
                    margin: 4px 0;
                    border: 1px solid #bbdefb;
                }
                .source-link:hover {
                    background-color: #bbdefb;
                    text-decoration: none;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Legal Entity Due Diligence Report</h1>
            </div>

            <div class="entity-info">
                <h2>Entity Information</h2>
                <table>
                    <tr><th>Entity Name</th><td>{{ legal_name }}</td></tr>
                    <tr><th>LEI Number</th><td>{{ lei_number }}</td></tr>
                    <tr><th>Products</th><td>{{ products }}</td></tr>
                    <tr><th>Check Date</th><td>{{ created_at }}</td></tr>
                    <tr><th>Status</th><td>{{ status }}</td></tr>
                    <tr><th>Risk Assessment</th><td>{{ risk_assessment }}</td></tr>
                </table>
            </div>

            <h2>Due Diligence Check Results</h2>

            {% for check_name, check_result in checks %}
            {% if check_result %}
            <div class="check-result status-{{ check_result.status.lower() }}">
                <h3>{{ check_name }}</h3>
                <p><strong>Status:</strong> {{ check_result.status }}</p>
                <p><strong>Confidence Score:</strong> <span class="confidence-score">{{ "%.2f"|format(check_result.confidence_score) }}</span></p>
                <p><strong>Summary:</strong> {{ check_result.summary }}</p>

                {% set details = check_result.details or {} %}
                {% set primary_sources = details.primary_sources or [] %}
                {% set legal_citations = details.legal_citations or [] %}
                {% set documentary_evidence = details.documentary_evidence_summary %}
                {% set audit_trail = details.audit_trail %}
                {% set compliance_framework = details.compliance_framework %}

                <!-- Documentary Evidence & Legal Authority -->
                {% if primary_sources or legal_citations or documentary_evidence %}
                <div class="evidence-section" style="background-color: #f8f9fa; padding: 15px; margin: 15px 0; border-radius: 5px;">
                    <h4>📄 Documentary Evidence & Legal Authority</h4>

                    {% if primary_sources %}
                    <div>
                        <strong>Primary Sources:</strong>
                        <ul>
                        {% for source in primary_sources %}
                            <li>
                                <strong>{{ source.source_type or 'Unknown' }}:</strong> {{ source.citation or source.document_name or 'N/A' }}
                                {% if source.relevance %}<br><em>{{ source.relevance }}</em>{% endif %}
                                {% if source.authority %}<br><small>Authority: {{ source.authority }}</small>{% endif %}
                                {% if source.url %}<br><a href="{{ source.url }}" target="_blank" rel="noopener noreferrer" class="source-link">🔗 View Source</a>{% endif %}
                            </li>
                        {% endfor %}
                        </ul>
                    </div>
                    {% endif %}

                    {% if legal_citations %}
                    <div>
                        <strong>Legal Citations:</strong>
                        <ul>
                        {% for citation in legal_citations %}
                            <li>
                                <strong>{{ citation.statute or citation.regulation or 'N/A' }}</strong>
                                {% if citation.section %} - {{ citation.section }}{% endif %}
                                <br><small>Authority: {{ citation.authority or 'N/A' }}</small>
                                {% if citation.relevance %}<br><em>{{ citation.relevance }}</em>{% endif %}
                                {% if citation.url %}<br><a href="{{ citation.url }}" target="_blank" rel="noopener noreferrer" class="source-link">🔗 View Legal Source</a>{% endif %}
                            </li>
                        {% endfor %}
                        </ul>
                    </div>
                    {% endif %}

                    {% if documentary_evidence %}
                    <div>
                        <strong>Evidence Strength Assessment:</strong>
                        <ul>
                            <li>Sources Consulted: {{ documentary_evidence.sources_consulted or 'N/A' }}</li>
                            <li>Legal Authorities: {{ documentary_evidence.legal_authorities_referenced or documentary_evidence.official_documents_referenced or 'N/A' }}</li>
                            <li>Evidence Strength: {{ documentary_evidence.evidence_strength or 'N/A' }}</li>
                        </ul>
                        {% if documentary_evidence.additional_documentation_required %}
                        <div style="background-color: #fff3cd; padding: 10px; border-radius: 3px; margin-top: 10px;">
                            <strong>Additional Documentation Required:</strong>
                            <ul>
                            {% for doc in documentary_evidence.additional_documentation_required %}
                                <li>{{ doc }}</li>
                            {% endfor %}
                            </ul>
                        </div>
                        {% endif %}
                    </div>
                    {% endif %}
                </div>
                {% endif %}

                <!-- Audit Trail & Methodology -->
                {% if audit_trail %}
                <div class="audit-section" style="background-color: #e8f4f8; padding: 15px; margin: 15px 0; border-radius: 5px;">
                    <h4>🔍 Audit Trail & Methodology</h4>
                    {% if audit_trail.methodology %}
                    <p><strong>Methodology:</strong> {{ audit_trail.methodology }}</p>
                    {% endif %}

                    {% if audit_trail.data_sources_accessed %}
                    <div>
                        <strong>Data Sources:</strong>
                        <ul>
                        {% for source in audit_trail.data_sources_accessed %}
                            <li>{{ source }}</li>
                        {% endfor %}
                        </ul>
                    </div>
                    {% endif %}

                    {% if audit_trail.limitations_identified %}
                    <div style="background-color: #fff3cd; padding: 10px; border-radius: 3px; margin-top: 10px;">
                        <strong>Analysis Limitations:</strong>
                        <ul>
                        {% for limitation in audit_trail.limitations_identified %}
                            <li>{{ limitation }}</li>
                        {% endfor %}
                        </ul>
                    </div>
                    {% endif %}
                </div>
                {% endif %}

                <!-- Regulatory Compliance Framework -->
                {% if compliance_framework %}
                <div class="compliance-section" style="background-color: #e8f5e8; padding: 15px; margin: 15px 0; border-radius: 5px;">
                    <h4>⚖️ Regulatory Compliance Framework</h4>

                    {% if compliance_framework.applicable_regulations %}
                    <div>
                        <strong>Applicable Regulations:</strong>
                        <ul>
                        {% for reg in compliance_framework.applicable_regulations %}
                            <li>{{ reg }}</li>
                        {% endfor %}
                        </ul>
                    </div>
                    {% endif %}

                    {% if compliance_framework.regulatory_authorities %}
                    <div>
                        <strong>Regulatory Authorities:</strong>
                        <ul>
                        {% for auth in compliance_framework.regulatory_authorities %}
                            <li>{{ auth }}</li>
                        {% endfor %}
                        </ul>
                    </div>
                    {% endif %}

                    {% if compliance_framework.documentation_requirements %}
                    <div style="background-color: #d4edda; padding: 10px; border-radius: 3px; margin-top: 10px;">
                        <strong>Documentation Requirements:</strong>
                        <ul>
                        {% for req in compliance_framework.documentation_requirements %}
                            <li>{{ req }}</li>
                        {% endfor %}
                        </ul>
                    </div>
                    {% endif %}
                </div>
                {% endif %}

                {% if check_result.limitations %}
                <h4>Limitations:</h4>
                <ul>
                    {% for limitation in check_result.limitations %}
                    <li>{{ limitation }}</li>
                    {% endfor %}
                </ul>
                {% endif %}

                {% if check_result.recommendations %}
                <h4>Recommendations:</h4>
                <ul>
                    {% for rec in check_result.recommendations %}
                    <li>{{ rec }}</li>
                    {% endfor %}
                </ul>
                {% endif %}
            </div>
            {% endif %}
            {% endfor %}

            {% if recommendations %}
            <div class="recommendations">
                <h2>Overall Recommendations</h2>
                <ul>
                    {% for rec in recommendations %}
                    <li>{{ rec }}</li>
                    {% endfor %}
                </ul>
            </div>
            {% endif %}

            <div class="footer">
                <p>Report generated on {{ generation_time }} by Legal Entity Due Diligence System</p>
            </div>
        </body>
        </html>
        """

        template = Template(template_str)

        # Prepare check results
        checks = [
            ("Entity Classification", due_diligence_check.entity_classification_result),
            ("Jurisdiction", due_diligence_check.jurisdiction_result),
            ("Authority", due_diligence_check.authority_result),
            ("Capacity", due_diligence_check.capacity_result),
            ("Legal Opinion", due_diligence_check.legal_opinion_result)
        ]

        recommendations = []
        if due_diligence_check.recommendations:
            recommendations = [rec.strip() for rec in due_diligence_check.recommendations.split('\n') if rec.strip()]

        html_content = template.render(
            legal_name=due_diligence_check.legal_name,
            lei_number=due_diligence_check.lei_number,
            products=", ".join(due_diligence_check.products),
            created_at=due_diligence_check.created_at.strftime("%Y-%m-%d %H:%M"),
            status=due_diligence_check.status.upper(),
            risk_assessment=due_diligence_check.risk_assessment or "N/A",
            checks=checks,
            recommendations=recommendations,
            generation_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        return html_content

    async def generate_json_report(self, due_diligence_check) -> str:
        """Generate JSON report"""

        report_data = {
            "entity_information": {
                "legal_name": due_diligence_check.legal_name,
                "lei_number": due_diligence_check.lei_number,
                "products": due_diligence_check.products,
                "check_date": due_diligence_check.created_at.isoformat(),
                "status": due_diligence_check.status,
                "risk_assessment": due_diligence_check.risk_assessment
            },
            "check_results": {
                "entity_classification": self._enhance_result_data(due_diligence_check.entity_classification_result),
                "jurisdiction": self._enhance_result_data(due_diligence_check.jurisdiction_result),
                "authority": self._enhance_result_data(due_diligence_check.authority_result),
                "capacity": self._enhance_result_data(due_diligence_check.capacity_result),
                "legal_opinion": self._enhance_result_data(due_diligence_check.legal_opinion_result)
            },
            "overall_assessment": {
                "risk_level": due_diligence_check.risk_assessment,
                "recommendations": due_diligence_check.recommendations.split('\n') if due_diligence_check.recommendations else [],
                "sources_checked": due_diligence_check.sources_checked or [],
                "evidence_documents": due_diligence_check.evidence_documents or []
            },
            "metadata": {
                "report_generated": datetime.now().isoformat(),
                "system_version": "1.0.0",
                "check_id": due_diligence_check.id
            }
        }

        return json.dumps(report_data, indent=2, ensure_ascii=False)

    def _enhance_result_data(self, result_data):
        """Enhance result data to include all comprehensive details for JSON export"""
        if not result_data:
            return None

        # Return the complete result data as-is, ensuring all nested details are preserved
        return result_data