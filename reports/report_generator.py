import datetime
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from config import Config

logger = logging.getLogger(__name__)

class ReportGenerator:
    """
    Generates professional executive audit reports in PDF and Excel formats.
    Includes overall scores, dimensional breakdowns, column metrics,
    issue diagnostics, AI insights, and cleaning audit logs.
    """

    @classmethod
    def generate_pdf_report(
        cls,
        session_id: str,
        dataset_name: str,
        overview: Dict[str, Any],
        scores: Dict[str, Any],
        issues: List[Dict[str, Any]],
        ai_understanding: Optional[Dict[str, Any]],
        ai_explanations: Optional[Dict[str, Any]],
        cleaning_audit: Optional[List[Dict[str, Any]]] = None
    ) -> Path:
        """
        Creates a polished, multi-page PDF audit report with ReportLab.
        """
        output_path = Config.OUTPUT_FOLDER / f"DataGuard_Report_{session_id}.pdf"
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        # Custom palette: White and Dark-Blue
        primary_color = colors.HexColor("#0f2744")
        secondary_color = colors.HexColor("#1b4b72")
        accent_color = colors.HexColor("#0d6efd")
        light_bg = colors.HexColor("#f8fafc")
        border_color = colors.HexColor("#cbd5e1")

        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=22,
            leading=26,
            textColor=primary_color,
            spaceAfter=4
        )
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#64748b"),
            spaceAfter=15
        )
        section_style = ParagraphStyle(
            "DocSection",
            parent=styles["Heading2"],
            fontSize=14,
            leading=18,
            textColor=primary_color,
            spaceBefore=12,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            "DocBody",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#1e293b")
        )
        small_bold = ParagraphStyle(
            "SmallBold",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            fontName="Helvetica-Bold",
            textColor=primary_color
        )

        story = []

        # 1. Header & Title Banner
        story.append(Paragraph("🛡️ DATAGUARD AI – DATA QUALITY AUDIT REPORT", title_style))
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        story.append(Paragraph(f"<b>Dataset:</b> {dataset_name} &nbsp;|&nbsp; <b>Session ID:</b> {session_id} &nbsp;|&nbsp; <b>Generated:</b> {now_str}", subtitle_style))
        story.append(Spacer(1, 10))

        # 2. Executive Summary Cards Table
        overall_score = scores.get("overall_score", 100.0)
        health = scores.get("health", "Good")
        dim = scores.get("dimensions", {})

        summary_data = [
            [
                Paragraph("<b>OVERALL QUALITY SCORE</b>", small_bold),
                Paragraph("<b>COMPLETENESS (25%)</b>", small_bold),
                Paragraph("<b>UNIQUENESS (20%)</b>", small_bold),
                Paragraph("<b>VALIDITY (30%)</b>", small_bold),
                Paragraph("<b>CONSISTENCY (25%)</b>", small_bold)
            ],
            [
                Paragraph(f"<font size=16 color='#0f2744'><b>{overall_score}%</b></font><br/>Rating: <b>{health}</b>", body_style),
                Paragraph(f"<font size=13 color='#1b4b72'><b>{dim.get('completeness', 100)}%</b></font>", body_style),
                Paragraph(f"<font size=13 color='#1b4b72'><b>{dim.get('uniqueness', 100)}%</b></font>", body_style),
                Paragraph(f"<font size=13 color='#1b4b72'><b>{dim.get('validity', 100)}%</b></font>", body_style),
                Paragraph(f"<font size=13 color='#1b4b72'><b>{dim.get('consistency', 100)}%</b></font>", body_style),
            ]
        ]

        summary_table = Table(summary_data, colWidths=[130, 100, 100, 100, 110])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), light_bg),
            ('BOX', (0, 0), (-1, -1), 1, border_color),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 15))

        # 3. AI Dataset Understanding
        if ai_understanding:
            story.append(Paragraph("🤖 AI Dataset Understanding & Inferred Domain", section_style))
            domain_name = ai_understanding.get("probable_domain", "Structured Data")
            domain_desc = ai_understanding.get("domain_description", "")
            story.append(Paragraph(f"<b>Inferred Domain:</b> {domain_name}<br/>{domain_desc}", body_style))
            story.append(Spacer(1, 10))

        # 4. Column Level Quality Breakdown
        story.append(Paragraph("📊 Column-Level Quality Breakdown", section_style))
        col_scores = scores.get("column_scores", {})
        col_headers = [
            Paragraph("<b>Column</b>", small_bold),
            Paragraph("<b>Quality</b>", small_bold),
            Paragraph("<b>Completeness</b>", small_bold),
            Paragraph("<b>Uniqueness</b>", small_bold),
            Paragraph("<b>Validity</b>", small_bold),
            Paragraph("<b>Consistency</b>", small_bold),
            Paragraph("<b>Health</b>", small_bold)
        ]
        col_rows = [col_headers]

        for col_name, c_data in list(col_scores.items())[:25]:
            col_rows.append([
                Paragraph(str(col_name)[:22], body_style),
                Paragraph(f"<b>{c_data.get('score')}%</b>", body_style),
                Paragraph(f"{c_data.get('completeness')}%", body_style),
                Paragraph(f"{c_data.get('uniqueness')}%", body_style),
                Paragraph(f"{c_data.get('validity')}%", body_style),
                Paragraph(f"{c_data.get('consistency')}%", body_style),
                Paragraph(f"<b>{c_data.get('health')}</b>", body_style)
            ])

        col_table = Table(col_rows, colWidths=[120, 65, 75, 75, 70, 75, 60])
        col_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, border_color),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, light_bg]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(col_table)
        story.append(Spacer(1, 15))

        # 5. Detected Issues and Anomalies
        story.append(Paragraph("⚠️ Detected Issues & AI Explanations", section_style))
        if not issues:
            story.append(Paragraph("<i>No data quality issues or anomalies detected. All rules passed!</i>", body_style))
        else:
            issue_headers = [
                Paragraph("<b>Severity</b>", small_bold),
                Paragraph("<b>Category</b>", small_bold),
                Paragraph("<b>Column</b>", small_bold),
                Paragraph("<b>Affected Records</b>", small_bold),
                Paragraph("<b>Title & Diagnostic Details</b>", small_bold)
            ]
            issue_rows = [issue_headers]
            for iss in issues[:30]:
                sev = iss.get("severity", "medium").upper()
                sev_color = "#dc3545" if sev == "HIGH" else ("#ffc107" if sev == "MEDIUM" else "#0d6efd")
                issue_rows.append([
                    Paragraph(f"<font color='{sev_color}'><b>{sev}</b></font>", body_style),
                    Paragraph(iss.get("category", "General").title(), body_style),
                    Paragraph(str(iss.get("column") or "Whole File")[:18], body_style),
                    Paragraph(f"{iss.get('affected_count')} ({iss.get('affected_pct', 0)}%)", body_style),
                    Paragraph(f"<b>{iss.get('title')}</b><br/>{iss.get('description', '')}", body_style)
                ])

            issues_table = Table(issue_rows, colWidths=[65, 75, 90, 95, 215])
            issues_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), secondary_color),
                ('GRID', (0, 0), (-1, -1), 0.5, border_color),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, light_bg]),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(issues_table)

        # 6. Cleaning Actions Audit Log (if applicable)
        if cleaning_audit:
            story.append(Spacer(1, 15))
            story.append(Paragraph("🧹 Data Sanitization & Cleaning Audit Log", section_style))
            audit_headers = [
                Paragraph("<b>Operation</b>", small_bold),
                Paragraph("<b>Target Column</b>", small_bold),
                Paragraph("<b>Records Modified</b>", small_bold)
            ]
            audit_rows = [audit_headers]
            for action in cleaning_audit:
                audit_rows.append([
                    Paragraph(str(action.get("operation")), body_style),
                    Paragraph(str(action.get("column")), body_style),
                    Paragraph(str(action.get("modified_rows", 0)), body_style)
                ])

            audit_table = Table(audit_rows, colWidths=[240, 150, 150])
            audit_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f766e")),
                ('GRID', (0, 0), (-1, -1), 0.5, border_color),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, light_bg]),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(audit_table)

        # Build document
        doc.build(story)
        return output_path

    @classmethod
    def generate_excel_summary(
        cls,
        session_id: str,
        dataset_name: str,
        overview: Dict[str, Any],
        scores: Dict[str, Any],
        issues: List[Dict[str, Any]],
        ai_understanding: Optional[Dict[str, Any]],
        cleaning_audit: Optional[List[Dict[str, Any]]] = None
    ) -> Path:
        """
        Creates an executive multi-sheet Excel workbook using openpyxl.
        """
        output_path = Config.OUTPUT_FOLDER / f"DataGuard_Summary_{session_id}.xlsx"
        wb = Workbook()

        # Styles
        header_fill = PatternFill(start_color="0F2744", end_color="0F2744", fill_type="solid")
        sub_header_fill = PatternFill(start_color="1B4B72", end_color="1B4B72", fill_type="solid")
        zebra_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        title_font = Font(name="Calibri", size=14, bold=True, color="0F2744")
        bold_font = Font(name="Calibri", size=10, bold=True)
        regular_font = Font(name="Calibri", size=10)
        thin_border = Border(
            left=Side(style='thin', color='CBD5E1'),
            right=Side(style='thin', color='CBD5E1'),
            top=Side(style='thin', color='CBD5E1'),
            bottom=Side(style='thin', color='CBD5E1')
        )

        # ---------------- SHEET 1: Executive Summary ----------------
        ws1 = wb.active
        ws1.title = "Executive Summary"
        ws1.append(["DataGuard AI – Dataset Quality Audit Summary"])
        ws1["A1"].font = title_font

        ws1.append(["Generated:", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        ws1.append(["Dataset:", dataset_name])
        ws1.append(["Inferred Domain:", (ai_understanding or {}).get("probable_domain", "Unknown")])
        ws1.append([])

        ws1.append(["Overall Quality Score", f"{scores.get('overall_score', 100)}%"])
        ws1.append(["Overall Rating", scores.get("health", "Good")])
        ws1.append(["Formula Used", scores.get("formula", "")])
        ws1.append([])

        ws1.append(["Quality Dimension", "Weight", "Calculated Score"])
        dim = scores.get("dimensions", {})
        ws1.append(["Completeness", "25%", f"{dim.get('completeness', 100)}%"])
        ws1.append(["Uniqueness", "20%", f"{dim.get('uniqueness', 100)}%"])
        ws1.append(["Validity", "30%", f"{dim.get('validity', 100)}%"])
        ws1.append(["Consistency", "25%", f"{dim.get('consistency', 100)}%"])
        ws1.append([])

        ws1.append(["Dataset Overview Metric", "Value"])
        ws1.append(["Total Rows", overview.get("row_count", 0)])
        ws1.append(["Total Columns", overview.get("column_count", 0)])
        ws1.append(["Total Missing Cells", overview.get("total_missing_cells", 0)])
        ws1.append(["Duplicate Rows", overview.get("duplicate_rows_count", 0)])
        ws1.append(["Total Confirmed Issues", len([i for i in issues if not i.get("is_anomaly_only")])])
        ws1.append(["Total Statistical Anomalies", len([i for i in issues if i.get("is_anomaly_only")])])

        # Style Sheet 1 headers
        for row_idx in [9, 16]:
            for col_idx in range(1, 3):
                cell = ws1.cell(row=row_idx, column=col_idx)
                cell.fill = header_fill
                cell.font = header_font

        # ---------------- SHEET 2: Column Scores ----------------
        ws2 = wb.create_sheet(title="Column Quality Scores")
        headers2 = ["Column Name", "Overall Score", "Completeness", "Uniqueness", "Validity", "Consistency", "Health Rating", "Issue Count"]
        ws2.append(headers2)
        for col_idx in range(1, len(headers2) + 1):
            cell = ws2.cell(row=1, column=col_idx)
            cell.fill = header_fill
            cell.font = header_font

        row_num = 2
        for col_name, c_data in scores.get("column_scores", {}).items():
            ws2.append([
                col_name,
                c_data.get("score"),
                c_data.get("completeness"),
                c_data.get("uniqueness"),
                c_data.get("validity"),
                c_data.get("consistency"),
                c_data.get("health"),
                c_data.get("issues_count", 0)
            ])
            if row_num % 2 == 1:
                for c in range(1, len(headers2) + 1):
                    ws2.cell(row=row_num, column=c).fill = zebra_fill
            row_num += 1

        # ---------------- SHEET 3: Issues Log ----------------
        ws3 = wb.create_sheet(title="Detected Issues & Anomalies")
        headers3 = ["Issue ID", "Category", "Check Type", "Severity", "Target Column", "Affected Records", "Affected %", "Issue Title", "Description"]
        ws3.append(headers3)
        for col_idx in range(1, len(headers3) + 1):
            cell = ws3.cell(row=1, column=col_idx)
            cell.fill = sub_header_fill
            cell.font = header_font

        row_num = 2
        for iss in issues:
            ws3.append([
                iss.get("id"),
                iss.get("category", "").title(),
                iss.get("check_type"),
                iss.get("severity", "").upper(),
                iss.get("column") or "Entire Dataset",
                iss.get("affected_count", 0),
                iss.get("affected_pct", 0),
                iss.get("title"),
                iss.get("description")
            ])
            if row_num % 2 == 1:
                for c in range(1, len(headers3) + 1):
                    ws3.cell(row=row_num, column=c).fill = zebra_fill
            row_num += 1

        # ---------------- SHEET 4: Cleaning Audit ----------------
        if cleaning_audit:
            ws4 = wb.create_sheet(title="Cleaning Audit Log")
            headers4 = ["Action / Rule Applied", "Target Column", "Records Modified"]
            ws4.append(headers4)
            for col_idx in range(1, len(headers4) + 1):
                cell = ws4.cell(row=1, column=col_idx)
                cell.fill = header_fill
                cell.font = header_font

            for act in cleaning_audit:
                ws4.append([
                    act.get("operation"),
                    act.get("column"),
                    act.get("modified_rows", 0)
                ])

        # Auto-adjust column widths across all sheets
        for ws in wb.worksheets:
            for col in ws.columns:
                max_len = max(len(str(cell.value or '')) for cell in col)
                col_letter = col[0].column_letter
                ws.column_dimensions[col_letter].width = min(40, max(12, max_len + 3))

        wb.save(output_path)
        return output_path
