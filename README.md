# 🛡️ DataGuard AI – Autonomous Data Quality & Anomaly Detection Agent

**DataGuard AI** is a professional, general-purpose, AI-powered Data Quality and Anomaly Detection application. It autonomously inspects, profiles, detects defects, calculates deterministic multi-dimensional quality scores, leverages Google Gemini LLM for domain understanding and adaptive validation planning, and enables interactive, user-approved data cleaning with multi-format audit report generation.

---

## 🚀 Key Features

- **Domain-Independent Architecture:** Never hardcodes column names, business rules, or fixed dataset structures. Seamlessly handles E-Commerce, Human Resources, Banking & Finance, Healthcare, Inventory/Supply Chain, and more.
- **Robust Multi-Format Ingestion:** Supports CSV, XLSX, XLS, and JSON with automatic encoding detection (UTF-8, Latin-1, CP1252), delimiter sniffing (`,`, `;`, `\t`, `|`), and 1-based row index tracking to preserve original records.
- **Statistical Profiling & Type Inference:** Distinguishes physical types (integer, float, datetime, string, categorical) and semantic roles (identifier, email, phone, timestamp, measure, currency).
- **Google Gemini LLM Integration:** Uses the official `google-genai` SDK for dataset domain understanding, column meaning extraction, adaptive validation planning, and plain-language issue explanations.
- **Deterministic Issue Detection:** Ground truth calculated strictly in Python across:
  - Missing values & empty strings
  - Full duplicate records & key identifier duplicates
  - Statistical outliers (IQR & modified Z-score) isolated as anomalies
  - Invalid formats (RFC email syntax, unparseable timestamps)
  - Negative/impossible metrics in non-negative columns
  - Inconsistent whitespace & casing divergence
  - Cross-column chronological inversions (e.g., `start_date > end_date`)
- **Interactive Cleaning Console:** Live before-and-after value preview. Approvals are granular—users can select which operations to apply without modifying the original raw file.
- **Enterprise Reporting:** Generates downloadable PDF audit reports (built with ReportLab), 4-sheet formatted Excel workbooks (built with openpyxl), and cleaned CSV/Excel datasets.

---

## 📐 Quality Scoring Methodology

DataGuard AI computes an overall quality score and individual column-level scores using this formula:

$$\text{Overall Quality Score} = 25\%\, \text{Completeness} + 20\%\, \text{Uniqueness} + 30\%\, \text{Validity} + 25\%\, \text{Consistency}$$

### Rules & Guardrails
1. **Dimension Weights:**
   - **Completeness (25%):** Penalizes nulls, NaNs, and blank/whitespace-only cells.
   - **Uniqueness (20%):** Penalizes duplicate rows and duplicate primary key identifiers.
   - **Validity (30%):** Penalizes invalid email/date formats, out-of-range metrics, negative values in non-negative fields, and mixed data types.
   - **Consistency (25%):** Penalizes untrimmed leading/trailing whitespace, categorical casing collisions, and cross-column chronological inversions.
2. **Double-Counting Prevention:** Records affected by multiple checks within a single quality dimension are deduplicated before scoring.
3. **No Non-Applicable Penalties:** Non-applicable checks do not penalize the score.
4. **Anomalies vs Confirmed Errors:** Statistical outliers are recorded as informational observations (`is_anomaly_only = True`) and do not drag down the quality score.

---

## 🛠️ Technology Stack

- **Backend:** Python 3.12, Flask 3.1
- **Data Science & ML:** Pandas, NumPy, SciPy, scikit-learn
- **AI / LLM:** Google Gemini API (`google-genai` SDK, Pydantic response validation)
- **Frontend:** HTML5, CSS3, JavaScript (ES6+), Bootstrap 5, Chart.js, Bootstrap Icons
- **Document Generation:** ReportLab (PDF), openpyxl (Excel)
- **Environment & Testing:** python-dotenv, Pytest

---

## 📂 Project Structure

```
AI-Data-Quality-Agent/
├── app.py                     # Flask application & REST API routes
├── config.py                  # Central configuration & resource limits
├── conftest.py                # Pytest configuration & sys.path setup
├── requirements.txt           # Project dependencies
├── .env                       # Environment variables (API Key, ports)
├── .env.example               # Template environment configuration
├── .gitignore                 # Version control ignore rules
├── README.md                  # Documentation
│
├── agent/
│   ├── orchestrator.py        # Master AI agent orchestrator (Steps 1–9)
│   ├── dataset_context.py     # Session state & in-memory dataset manager
│   ├── rule_planner.py        # Reusable detector registry & check planner
│   └── result_manager.py      # Payload aggregator & JSON serializer
│
├── engine/
│   ├── ingestion.py           # Multi-format tabular file ingestion & encoding detector
│   ├── type_inference.py      # Physical & semantic regex/statistical type inferrer
│   ├── profiler.py            # Statistical distributions & summary engine
│   ├── missing_detector.py    # Completeness detector (nulls & blanks)
│   ├── duplicate_detector.py  # Uniqueness detector (duplicate rows & IDs)
│   ├── outlier_detector.py    # Statistical outlier detector (IQR & Z-score)
│   ├── validity_detector.py   # Validity detector (emails, dates, bounds, types)
│   ├── consistency_detector.py# Consistency detector (whitespace, casing)
│   ├── integrity_detector.py  # Structural & relational chronological detector
│   └── scoring_engine.py      # Multi-dimensional quality scoring engine
│
├── ai/
│   ├── gemini_service.py      # Official google-genai client & heuristic fallback
│   ├── prompts.py             # Ground-truth constrained LLM prompts
│   └── response_validator.py  # Pydantic schemas for structured AI outputs
│
├── cleaning/
│   ├── cleaning_engine.py     # Interactive preview generator & batch cleaner
│   └── cleaning_rules.py      # Pure transformation functions
│
├── reports/
│   └── report_generator.py    # ReportLab PDF & openpyxl Excel report builder
│
├── templates/
│   └── index.html             # Bootstrap 5 SaaS dashboard template
│
├── static/
│   ├── css/style.css          # White & dark-blue theme custom styling
│   └── js/dashboard.js        # Dynamic UI controller & Chart.js logic
│
├── tests/
│   ├── test_profiler.py       # Type inference & profiler unit tests
│   ├── test_detectors.py      # Deterministic issue detector tests
│   ├── test_scoring.py        # Scoring formula & weight verification tests
│   ├── test_live_server.py    # Flask WSGI end-to-end integration tests
│   └── test_multiple_datasets.py # Cross-domain validation on 5 sample datasets
│
├── sample_datasets/
│   ├── online_store_orders.csv    # E-Commerce demo dataset (default)
│   ├── employees.csv              # Human Resources dataset
│   ├── financial_transactions.csv # Banking ledger dataset
│   ├── healthcare_patients.csv    # Clinical records dataset
│   ├── inventory_stock.csv        # Warehouse supply chain dataset
│   └── generate_samples.py        # Sample dataset generator script
│
├── uploads/                   # Staged upload directory
└── outputs/                   # Generated reports & cleaned datasets
```

---

## ⚡ Installation & Setup (PowerShell)

### 1. Clone or Open Workspace
```powershell
cd C:\Users\SreejaGopagani\Desktop\Chilly
```

### 2. Configure Environment Variables
Create or verify your `.env` file:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
SECRET_KEY=dataguard-ai-super-secret-key-2026
MAX_CONTENT_LENGTH=33554432
UPLOAD_FOLDER=uploads
OUTPUT_FOLDER=outputs
PORT=5000
HOST=127.0.0.1
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Run Automated Tests
Execute the full test suite (21 automated tests covering detectors, profiler, scoring, and cross-domain pipelines):
```powershell
python -m pytest -p no:anyio -v
```

### 5. Launch the Application
Start the Flask web server:
```powershell
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🧪 Demonstration & Testing Walkthrough

1. **Dashboard Home:** View system status and click **"New Dataset"** or **"Analyze A Dataset"**.
2. **Quick-Load Demo:** On the **Upload Dataset** tab, click **"Online Store Orders (Default Demo)"** (or upload your own CSV/XLSX/JSON file).
3. **Automated Profiling:** Switch to **Dataset Profile** to inspect inferred types, null counts, distinct counts, and sample values.
4. **Scoring Breakdown:** Open **Quality Overview** to see the 25/20/30/25 dimension scorecard and column-level quality matrix.
5. **Issues & Diagnostics:** View detected defects categorized with severity badges. Filter by category (Completeness, Uniqueness, Validity, Consistency, Anomaly) or severity.
6. **AI Insights:** Check the **AI Insights** tab for Gemini's inferred domain, column meanings, and executive action recommendations.
7. **Interactive Cleaning:**
   - Go to **Data Cleaning**.
   - Click **"Preview Before/After"** on any issue to see row-by-row before and after changes.
   - Select the operations to approve and click **"Apply Approved Cleanings"**.
   - Notice the quality score improve in real time!
8. **Reports & Exports:** Open **Reports & Exports** to download:
   - Official **PDF Audit Report**
   - Multi-sheet **Excel Quality Summary**
   - Cleaned **CSV or Excel Dataset**

---

## 🛡️ License

Built with pride for high-stakes enterprise data verification and quality assurance.
