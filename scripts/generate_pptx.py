import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def create_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    bg_path = os.path.abspath(r"template_assets\ppt\media\image1.jpeg")
    logo_path = os.path.abspath(r"template_assets\ppt\media\image2.png")

    blank_layout = prs.slide_layouts[6]  # completely blank slide

    # Brand Colors
    DARK_BLUE = RGBColor(14, 14, 44)       # #0E0E2C
    MUTED_TEXT = RGBColor(74, 74, 104)     # #4A4A68
    ACCENT_BLUE = RGBColor(28, 88, 214)    # #1C58D6
    ACCENT_RED = RGBColor(217, 51, 63)     # #D9333F
    CARD_BG = RGBColor(248, 250, 253)      # #F8FAFD
    CARD_BORDER = RGBColor(220, 228, 242)  # #DCE4F2
    WHITE = RGBColor(255, 255, 255)
    GREEN = RGBColor(16, 149, 106)        # #10956A

    def add_base_slide(title_text=""):
        slide = prs.slides.add_slide(blank_layout)

        # 1. Background image
        if os.path.exists(bg_path):
            slide.shapes.add_picture(bg_path, 0, 0, prs.slide_width, prs.slide_height)

        # 2. Logo at top right
        if os.path.exists(logo_path):
            slide.shapes.add_picture(logo_path, Inches(11.0), Inches(0.32), Inches(1.85), Inches(0.42))

        # 3. Kicker / Subtitle (Agivant Technologies)
        kicker_box = slide.shapes.add_textbox(Inches(0.85), Inches(0.65), Inches(8.0), Inches(0.35))
        tf_k = kicker_box.text_frame
        tf_k.word_wrap = True
        tf_k.margin_left = tf_k.margin_top = tf_k.margin_right = tf_k.margin_bottom = 0
        p_k = tf_k.paragraphs[0]
        p_k.text = "AGIVANT TECHNOLOGIES"
        p_k.font.name = "Poppins"
        p_k.font.size = Pt(13)
        p_k.font.bold = True
        p_k.font.color.rgb = ACCENT_BLUE

        # 4. Slide Title
        if title_text:
            title_box = slide.shapes.add_textbox(Inches(0.85), Inches(1.05), Inches(9.8), Inches(0.95))
            tf_t = title_box.text_frame
            tf_t.word_wrap = True
            tf_t.margin_left = tf_t.margin_top = tf_t.margin_right = tf_t.margin_bottom = 0
            p_t = tf_t.paragraphs[0]
            p_t.text = title_text
            p_t.font.name = "Poppins"
            p_t.font.size = Pt(32)
            p_t.font.bold = True
            p_t.font.color.rgb = DARK_BLUE

        # 5. Footer
        footer_box = slide.shapes.add_textbox(Inches(0.85), Inches(6.8), Inches(10.0), Inches(0.35))
        tf_f = footer_box.text_frame
        tf_f.margin_left = tf_f.margin_top = tf_f.margin_right = tf_f.margin_bottom = 0
        p_f = tf_f.paragraphs[0]
        p_f.text = "November 2026 | Agivant Technologies — DataGuard AI"
        p_f.font.name = "Poppins"
        p_f.font.size = Pt(11)
        p_f.font.color.rgb = MUTED_TEXT

        return slide

    def add_card(slide, left, top, width, height, title, items, badge_text="", accent_color=ACCENT_BLUE):
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = CARD_BG
        shape.line.color.rgb = CARD_BORDER
        shape.line.width = Pt(1.2)

        tf = shape.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.25)
        tf.margin_top = Inches(0.22)
        tf.margin_right = Inches(0.25)
        tf.margin_bottom = Inches(0.2)

        # Header paragraph
        p_title = tf.paragraphs[0]
        p_title.text = title
        p_title.font.name = "Poppins"
        p_title.font.size = Pt(17)
        p_title.font.bold = True
        p_title.font.color.rgb = DARK_BLUE
        p_title.space_after = Pt(8)

        for item in items:
            p = tf.add_paragraph()
            p.font.name = "Poppins"
            p.font.size = Pt(13)
            p.space_after = Pt(5)

            if isinstance(item, tuple):
                bold_prefix, text_rest = item
                r_bold = p.add_run()
                r_bold.text = bold_prefix + " "
                r_bold.font.bold = True
                r_bold.font.color.rgb = DARK_BLUE
                r_bold.font.size = Pt(13)

                r_rest = p.add_run()
                r_rest.text = text_rest
                r_rest.font.bold = False
                r_rest.font.color.rgb = MUTED_TEXT
                r_rest.font.size = Pt(13)
            else:
                r = p.add_run()
                r.text = item
                r.font.color.rgb = MUTED_TEXT
                r.font.size = Pt(13)

        return shape

    # ==========================================
    # SLIDE 1: Title Slide
    # ==========================================
    s1 = prs.slides.add_slide(blank_layout)
    if os.path.exists(bg_path):
        s1.shapes.add_picture(bg_path, 0, 0, prs.slide_width, prs.slide_height)
    if os.path.exists(logo_path):
        s1.shapes.add_picture(logo_path, Inches(10.8), Inches(0.4), Inches(2.0), Inches(0.46))

    # Kicker
    k_box = s1.shapes.add_textbox(Inches(0.9), Inches(1.5), Inches(10.0), Inches(0.4))
    p = k_box.text_frame.paragraphs[0]
    p.text = "AGIVANT TECHNOLOGIES"
    p.font.name = "Poppins"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = ACCENT_BLUE

    # Title
    t_box = s1.shapes.add_textbox(Inches(0.9), Inches(2.0), Inches(11.0), Inches(1.6))
    p = t_box.text_frame.paragraphs[0]
    p.text = "DataGuard AI"
    p.font.name = "Poppins"
    p.font.size = Pt(56)
    p.font.bold = True
    p.font.color.rgb = DARK_BLUE

    # Subtitle
    sub_box = s1.shapes.add_textbox(Inches(0.9), Inches(3.7), Inches(11.0), Inches(1.2))
    tf_sub = sub_box.text_frame
    tf_sub.word_wrap = True
    p = tf_sub.paragraphs[0]
    p.text = "Autonomous AI-Powered Data Quality & Anomaly Detection Agent"
    p.font.name = "Poppins"
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = ACCENT_RED

    p2 = tf_sub.add_paragraph()
    p2.text = "Deterministic Profiling, Multi-Dimensional Scoring, Gemini Intelligence & Human-in-the-Loop Governance"
    p2.font.name = "Poppins"
    p2.font.size = Pt(15)
    p2.font.color.rgb = MUTED_TEXT
    p2.space_before = Pt(8)

    # Metadata badges
    m_box = s1.shapes.add_textbox(Inches(0.9), Inches(5.6), Inches(10.0), Inches(0.8))
    tf_m = m_box.text_frame
    p_meta = tf_m.paragraphs[0]
    p_meta.text = "Author: Sreeja Gopagani  |  Organization: Agivant Technologies  |  November 2026"
    p_meta.font.name = "Poppins"
    p_meta.font.size = Pt(13)
    p_meta.font.color.rgb = DARK_BLUE
    p_meta.font.bold = True

    # ==========================================
    # SLIDE 2: Problem Statement
    # ==========================================
    s2 = add_base_slide("Problem Statement: The Enterprise Data Quality Crisis")

    # Left Card
    add_card(s2, Inches(0.85), Inches(2.05), Inches(5.6), Inches(4.5),
             "Industry Realities & Pain Points",
             [
                 ("• $3.1 Trillion Annual Cost:", "IBM & Gartner report massive global losses due to poor data quality in analytics and ML."),
                 ("• Silent Failure in Pipelines:", "Null values, duplicate records, and invalid formats slip past raw ingestion undetected."),
                 ("• The 80% Time Sink:", "Data engineers spend up to 80% of their work week writing ad-hoc, manual scripts to clean dirty datasets."),
                 ("• Unsafe Cloud LLM Audits:", "Blindly uploading sensitive raw datasets to cloud models causes severe GDPR & HIPAA privacy violations.")
             ])

    # Right Card
    add_card(s2, Inches(6.8), Inches(2.05), Inches(5.6), Inches(4.5),
             "Critical Industry Gaps",
             [
                 ("• Lack of Mathematical Precision:", "Pure LLM tools hallucinate numbers, miscount rows, and fail on large tabular records."),
                 ("• Rigid Rule Engines:", "Traditional data linters break across different business domains without continuous manual tuning."),
                 ("• Black-Box Automation:", "Automated cleaning often corrupts records by guessing replacements without human approval."),
                 ("• Compliance Risk:", "Enterprises need verifiable audit trails, version immutability, and executive-ready reporting.")
             ],
             accent_color=ACCENT_RED)

    # ==========================================
    # SLIDE 3: Proposed Solution - DataGuard AI
    # ==========================================
    s3 = add_base_slide("The Solution: DataGuard AI Autonomous Agent")

    add_card(s3, Inches(0.85), Inches(2.05), Inches(3.6), Inches(4.5),
             "1. Deterministic Engine",
             [
                 ("• Local Python Execution:", "Pandas, NumPy, and Scipy compute 100% exact statistics with zero hallucination."),
                 ("• Multi-Dimensional Profiling:", "Completeness, Uniqueness, Validity, and Consistency evaluated systematically."),
                 ("• Zero Cloud Transmission:", "Raw dataset records remain completely private in local memory.")
             ])

    add_card(s3, Inches(4.8), Inches(2.05), Inches(3.6), Inches(4.5),
             "2. Gemini Intelligence",
             [
                 ("• Context Understanding:", "Analyzes compact metadata to infer business domain and column semantics."),
                 ("• Validation Planning:", "Formulates tailored validation rules for financial, clinical, or retail datasets."),
                 ("• Executive Insights:", "Generates business impact summaries and recommended remediations.")
             ])

    add_card(s3, Inches(8.75), Inches(2.05), Inches(3.6), Inches(4.5),
             "3. Human-in-the-Loop",
             [
                 ("• Interactive Console:", "Review before-and-after transformation previews for every single defect."),
                 ("• Row-by-Row Custom Edits:", "Inspect exact row numbers and enter manual replacement values."),
                 ("• Zero Destructive Overwrites:", "Original data is preserved while producing audited sanitized outputs.")
             ])

    # ==========================================
    # SLIDE 4: Standardized Quality Scoring Model
    # ==========================================
    s4 = add_base_slide("Comprehensive 4-Dimension Quality Scoring")

    # Formula banner box
    f_shape = s4.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.85), Inches(2.0), Inches(11.55), Inches(0.85))
    f_shape.fill.solid()
    f_shape.fill.fore_color.rgb = DARK_BLUE
    f_shape.line.fill.background()
    p_f = f_shape.text_frame.paragraphs[0]
    p_f.text = "Overall Quality Score = 0.25 × Completeness + 0.20 × Uniqueness + 0.30 × Validity + 0.25 × Consistency"
    p_f.alignment = PP_ALIGN.CENTER
    p_f.font.name = "Poppins"
    p_f.font.size = Pt(16)
    p_f.font.bold = True
    p_f.font.color.rgb = WHITE

    add_card(s4, Inches(0.85), Inches(3.05), Inches(2.7), Inches(3.5),
             "Completeness (25%)",
             [
                 ("Focus:", "Missing & Null values."),
                 ("Method:", "Detects NaN, None, null, empty strings, whitespace-only, and placeholder tokens (N/A, unknown)."),
                 ("Target:", "Ensures every mandatory field has usable data.")
             ])

    add_card(s4, Inches(3.8), Inches(3.05), Inches(2.7), Inches(3.5),
             "Uniqueness (20%)",
             [
                 ("Focus:", "Entity duplication."),
                 ("Method:", "Evaluates primary key collision and multi-column composite duplicate records."),
                 ("Target:", "Eliminates duplicate ledger records, orders, and user accounts.")
             ])

    add_card(s4, Inches(6.75), Inches(3.05), Inches(2.7), Inches(3.5),
             "Validity (30%)",
             [
                 ("Focus:", "Format & bounds."),
                 ("Method:", "Validates emails, phone numbers, postal codes, regex patterns, and numeric ranges."),
                 ("Target:", "Guarantees data conforms to strict type definitions.")
             ])

    add_card(s4, Inches(9.7), Inches(3.05), Inches(2.7), Inches(3.5),
             "Consistency (25%)",
             [
                 ("Focus:", "Relational rules."),
                 ("Method:", "Evaluates cross-column business invariants (e.g. Unit Cost ≤ Retail Price, Hire Date ≤ Term Date)."),
                 ("Target:", "Ensures internal logical coherence.")
             ])

    # ==========================================
    # SLIDE 5: Anomaly & Outlier Detection Engine
    # ==========================================
    s5 = add_base_slide("Multi-Method Anomaly & Outlier Detection")

    add_card(s5, Inches(0.85), Inches(2.05), Inches(5.6), Inches(4.5),
             "Statistical & Non-Parametric Detection",
             [
                 ("• Z-Score Parametric Profiling:", "Flags numeric observations where |z| > 3.0 standard deviations from Gaussian mean."),
                 ("• Interquartile Range (IQR):", "Tukey's fences [Q1 - 1.5×IQR, Q3 + 1.5×IQR] detect skewed financial and operational anomalies."),
                 ("• Frequency Distribution Outliers:", "Rare category frequency detection finds erroneous typos and mislabeled classification values."),
                 ("• Exact Row-Level Mapping:", "Every anomaly is tagged with its exact dataset row number (e.g., Row #42, Row #107).")
             ])

    add_card(s5, Inches(6.8), Inches(2.05), Inches(5.6), Inches(4.5),
             "Semantic & Relational Invariants",
             [
                 ("• Temporal Order Validation:", "Detects logical time paradoxes (hire date occurring after resignation/termination)."),
                 ("• Business Constraint Rules:", "Flags impossible economic conditions (negative product prices, cost greater than price)."),
                 ("• Physiological Boundaries:", "Checks human domain thresholds (e.g., age > 120, blood pressure > 250)."),
                 ("• Structural Integrity:", "Detects trailing spaces, mixed uppercase/lowercase casing, and unparseable date formats.")
             ])

    # ==========================================
    # SLIDE 6: Privacy-First AI & Zero-Raw-Data Architecture
    # ==========================================
    s6 = add_base_slide("Privacy-First AI: Zero Raw Data Sent to Cloud")

    add_card(s6, Inches(0.85), Inches(2.05), Inches(5.6), Inches(4.5),
             "What Stays 100% Local (Private Memory)",
             [
                 ("✔ Entire Raw Dataset Records:", "Tens of thousands of rows stay strictly inside local Python/Pandas RAM."),
                 ("✔ Deterministic Calculations:", "Missing checks, regex filters, duplicate scans, and math scoring run locally."),
                 ("✔ Individual Anomaly Indexing:", "Specific defect rows and cell contents are identified without cloud APIs."),
                 ("✔ Cleaning & Transformations:", "All data imputations and sanitizations execute on local disk/memory.")
             ],
             accent_color=GREEN)

    add_card(s6, Inches(6.8), Inches(2.05), Inches(5.6), Inches(4.5),
             "What Is Sent to Gemini LLM (Metadata Only)",
             [
                 ("• Schema & Column Names:", "High-level structure (e.g., 'customer_name', 'total_amount')."),
                 ("• Inferred Data Types:", "Column classifications (e.g., integer, float, date, email)."),
                 ("• Statistical Aggregates:", "Total row counts, null counts, min/max/median numbers."),
                 ("• Non-Sensitive Context Sample:", "3 to 5 anonymized values strictly to discern domain (e.g. Retail vs Healthcare).")
             ])

    # ==========================================
    # SLIDE 7: Human-in-the-Loop (HITL) Cleaning Console
    # ==========================================
    s7 = add_base_slide("Interactive Human-in-the-Loop Data Cleaning")

    add_card(s7, Inches(0.85), Inches(2.05), Inches(3.6), Inches(4.5),
             "1. AI-Suggested Actions",
             [
                 ("• Intelligent Baselines:", "Median imputation for skewed numeric data; mode for categorical; constant fills for identifiers."),
                 ("• Standard Transforms:", "Title casing, whitespace stripping, date standardization, and duplicate row dropping."),
                 ("• Defect Attribution:", "Clear explanation of why each correction rule is recommended.")
             ])

    add_card(s7, Inches(4.8), Inches(2.05), Inches(3.6), Inches(4.5),
             "2. Row-by-Row Custom Edits",
             [
                 ("• Individual Row Inspection:", "View specific defect rows (e.g., Row #107, Row #283) in a dedicated preview modal."),
                 ("• Granular Manual Overrides:", "Type custom values for specific individual rows rather than applying blanket fixes."),
                 ("• Live Diff Preview:", "Instant visual confirmation of Original (Before) vs. Corrected (After) data.")
             ])

    add_card(s7, Inches(8.75), Inches(2.05), Inches(3.6), Inches(4.5),
             "3. User Approval & Safety",
             [
                 ("• Zero Auto-Execution:", "All cleaning operations require explicit user approval (Pending Review by default)."),
                 ("• Batch or Selective Approvals:", "Approve specific fixes while rejecting unwanted modifications."),
                 ("• Non-Destructive Versioning:", "Original uploaded dataset is preserved untouched; sanitized data exported separately.")
             ])

    # ==========================================
    # SLIDE 8: Executive Reporting & Multi-Format Exports
    # ==========================================
    s8 = add_base_slide("Enterprise Audit Reports & Export Capabilities")

    add_card(s8, Inches(0.85), Inches(2.05), Inches(3.6), Inches(4.5),
             "Executive PDF Audit Reports",
             [
                 ("• High-Fidelity Vector PDF:", "Generated via ReportLab with corporate branding and typography."),
                 ("• Visual Score Gauge:", "Color-coded quality score meter and health distribution bars."),
                 ("• Defect Catalog:", "Detailed severity breakdown with identified row indices and suggested fixes."),
                 ("• Executive Summary:", "Gemini-generated risk analysis and business recommendations.")
             ])

    add_card(s8, Inches(4.8), Inches(2.05), Inches(3.6), Inches(4.5),
             "Structured Excel Workbooks",
             [
                 ("• Multi-Sheet Audit Log:", "Generated via OpenPyXL for deep spreadsheet inspection."),
                 ("• Dimension Breakdown:", "Exact numerical scores for Completeness, Uniqueness, Validity, Consistency."),
                 ("• Action Item Matrix:", "Categorized priority list of confirmed quality defects and potential anomalies.")
             ])

    add_card(s8, Inches(8.75), Inches(2.05), Inches(3.6), Inches(4.5),
             "Sanitized Dataset Exports",
             [
                 ("• Instant CSV Export:", "Fully transformed, verified dataset ready for downstream analytics."),
                 ("• Formatted Excel Export:", "Cleaned data formatted into native spreadsheet tables."),
                 ("• Full Reproducibility:", "Every cleaning transformation is logged with timestamp and operator record.")
             ])

    # ==========================================
    # SLIDE 9: Technical Architecture & Implementation
    # ==========================================
    s9 = add_base_slide("Technical Architecture & System Implementation")

    add_card(s9, Inches(0.85), Inches(2.05), Inches(3.6), Inches(4.5),
             "Backend Engine",
             [
                 ("• Framework:", "Python 3.12, Flask RESTful API."),
                 ("• Data Processing:", "Pandas, NumPy, Scipy."),
                 ("• Reporting Engines:", "ReportLab (PDF), OpenPyXL (Excel)."),
                 ("• Architecture:", "Modular service layers (Engine, AI, Cleaning, Reports, Orchestrator).")
             ])

    add_card(s9, Inches(4.8), Inches(2.05), Inches(3.6), Inches(4.5),
             "AI & LLM Services",
             [
                 ("• SDK:", "Official Google GenAI SDK (google-genai)."),
                 ("• Model:", "Gemini 3.5 Flash Lite (with fallback to Gemini 3.8 Flash)."),
                 ("• Strict Validation:", "Structured JSON schema validation and retry guards."),
                 ("• Resilience:", "Graceful offline fallback if API quota or connectivity is interrupted.")
             ])

    add_card(s9, Inches(8.75), Inches(2.05), Inches(3.6), Inches(4.5),
             "Frontend & Testing",
             [
                 ("• UI Framework:", "Clean SaaS responsive layout, Bootstrap 5, FontAwesome icons."),
                 ("• Visualizations:", "Chart.js dynamic gauges and column health distribution bars."),
                 ("• State Management:", "Vanilla JS async REST client with interactive modal overrides."),
                 ("• Verification:", "21 comprehensive automated Pytest test suites passing 100%.")
             ])

    # ==========================================
    # SLIDE 10: Multi-Domain Verification & Results
    # ==========================================
    s10 = add_base_slide("Proven Multi-Domain Verification")

    add_card(s10, Inches(0.85), Inches(2.05), Inches(5.6), Inches(2.1),
             "E-Commerce Retail Orders",
             [
                 ("Detected:", "Duplicate order IDs, invalid customer email formats, negative total amounts, casing errors."),
                 ("Resolution:", "Deduplication by key, regex sanitization, median price imputation.")
             ])

    add_card(s10, Inches(6.8), Inches(2.05), Inches(5.6), Inches(2.1),
             "Human Resources Workforce",
             [
                 ("Detected:", "Salary statistical outliers (Z > 3.0), temporal inversions (hire date after termination date)."),
                 ("Resolution:", "IQR salary cap, date logic swapping, title standardization.")
             ])

    add_card(s10, Inches(0.85), Inches(4.45), Inches(5.6), Inches(2.1),
             "Banking Ledger & Transactions",
             [
                 ("Detected:", "Negative transaction balances, duplicate transaction hashes, unparseable dates."),
                 ("Resolution:", "Absolute value conversion, hash deduplication, ISO timestamp conversion.")
             ])

    add_card(s10, Inches(6.8), Inches(4.45), Inches(5.6), Inches(2.1),
             "Healthcare Patient Telemetry",
             [
                 ("Detected:", "Physiologically impossible ages (>120), missing diagnosis codes, blood pressure outliers."),
                 ("Resolution:", "Human-in-the-loop manual clinical override, mode imputation.")
             ])

    # ==========================================
    # SLIDE 11: Summary & Strategic Roadmap
    # ==========================================
    s11 = add_base_slide("Summary & Strategic Product Roadmap")

    add_card(s11, Inches(0.85), Inches(2.05), Inches(5.6), Inches(4.5),
             "Current Accomplishments",
             [
                 ("✔ Domain-Independent Agent:", "Works seamlessly across CSV, XLSX, XLS, and JSON files."),
                 ("✔ Zero Hallucination:", "Deterministic mathematical scoring coupled with LLM contextual reasoning."),
                 ("✔ Absolute Privacy Guarantee:", "Zero raw records transmitted to cloud; 100% compliant."),
                 ("✔ Human-in-the-Loop Power:", "Row-by-row manual value overrides with before/after visual audit."),
                 ("✔ Production Ready:", "Comprehensive PDF, Excel, and sanitized data export capabilities.")
             ],
             accent_color=GREEN)

    add_card(s11, Inches(6.8), Inches(2.05), Inches(5.6), Inches(4.5),
             "Strategic Future Roadmap",
             [
                 ("• Cloud Warehouse Connectors:", "Direct read/write integrations with Snowflake, Google BigQuery, and Databricks."),
                 ("• Real-Time Stream Auditing:", "Kafka and Spark streaming anomaly detection for live IoT and payment feeds."),
                 ("• CI/CD Pipeline Gates:", "Automated data regression testing gates for dbt, Airflow, and Prefect workflows."),
                 ("• Autonomous Auto-Fix Models:", "Self-improving ML models trained on accepted human intervention overrides.")
             ])

    # Save presentation
    output_filename = "DataGuard_AI_Project_Presentation.pptx"
    prs.save(output_filename)
    print(f"Presentation saved successfully as: {output_filename}")
    return output_filename

if __name__ == "__main__":
    create_deck()
