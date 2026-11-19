import logging
import os
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

from config import Config
from agent.orchestrator import DataGuardAgent
from agent.dataset_context import DatasetSessionContext
from agent.result_manager import ResultManager
from engine.ingestion import IngestionError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("DataGuardAI")

app = Flask(__name__)
app.config.from_object(Config)

# Initialize Agent
agent = DataGuardAgent()

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@app.route("/")
def index():
    """Main SaaS Dashboard."""
    return render_template("index.html")

@app.route("/api/health", methods=["GET"])
def health():
    """System health check and Gemini status."""
    return jsonify({
        "status": "online",
        "gemini_connected": agent.gemini_service.is_connected,
        "gemini_model": agent.gemini_service.model_name
    })

@app.route("/api/sessions", methods=["GET"])
def list_sessions():
    """List recent dataset analysis sessions."""
    recent = DatasetSessionContext.list_recent_sessions(limit=10)
    return jsonify({"sessions": recent})

@app.route("/api/load-sample", methods=["POST"])
def load_sample():
    """Loads one of the pre-built sample datasets for quick demonstration."""
    data = request.get_json() or {}
    sample_name = data.get("sample_name", "online_store_orders.csv")
    user_context = data.get("user_context", "")

    sample_path = Config.SAMPLE_DATASETS_FOLDER / secure_filename(sample_name)
    if not sample_path.exists():
        # Check workspace root
        sample_path = Config.BASE_DIR / secure_filename(sample_name)

    if not sample_path.exists():
        return jsonify({"error": f"Sample dataset '{sample_name}' not found."}), 404

    try:
        session = agent.process_dataset(file_path=sample_path, user_context=user_context)
        payload = ResultManager.format_dashboard_payload(session)
        return jsonify({"success": True, "data": payload})
    except Exception as e:
        logger.exception("Failed to process sample dataset.")
        return jsonify({"error": str(e)}), 500

@app.route("/api/upload", methods=["POST"])
def upload_dataset():
    """Handles upload of CSV, XLSX, XLS, or JSON datasets."""
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    if not allowed_file(file.filename):
        return jsonify({
            "error": f"File type not allowed. Supported formats: {', '.join(Config.ALLOWED_EXTENSIONS)}"
        }), 400

    filename = secure_filename(file.filename)
    user_context = request.form.get("user_context", "").strip()

    upload_path = Config.UPLOAD_FOLDER / filename
    file.save(upload_path)

    try:
        session = agent.process_dataset(file_path=upload_path, user_context=user_context)
        payload = ResultManager.format_dashboard_payload(session)
        return jsonify({"success": True, "data": payload})
    except IngestionError as ie:
        return jsonify({"error": f"Ingestion Error: {str(ie)}"}), 422
    except Exception as e:
        logger.exception("Unexpected error during dataset processing.")
        return jsonify({"error": f"Internal Processing Error: {str(e)}"}), 500

@app.route("/api/session/<session_id>", methods=["GET"])
def get_session_data(session_id: str):
    """Retrieves full analysis payload for an existing session."""
    session = DatasetSessionContext.get_session(session_id)
    if not session:
        return jsonify({"error": f"Session '{session_id}' not found."}), 404

    payload = ResultManager.format_dashboard_payload(session)
    return jsonify({"success": True, "data": payload})

@app.route("/api/preview-cleaning/<session_id>/<issue_id>", methods=["GET"])
def preview_cleaning(session_id: str, issue_id: str):
    """Generates before-and-after sample rows for a specific issue."""
    try:
        preview = agent.preview_cleaning(session_id, issue_id)
        return jsonify({"success": True, "preview": preview})
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 404
    except Exception as e:
        logger.exception("Error creating preview.")
        return jsonify({"error": str(e)}), 500

@app.route("/api/apply-cleaning/<session_id>", methods=["POST"])
def apply_cleaning(session_id: str):
    """Applies user-approved cleaning fixes to generate a cleaned dataset."""
    data = request.get_json() or {}
    approved_ids = data.get("approved_issue_ids", [])
    manual_overrides = data.get("manual_overrides", {})

    if not approved_ids:
        return jsonify({"error": "No issues selected for cleaning."}), 400

    try:
        result = agent.execute_cleaning(session_id, approved_ids, manual_overrides=manual_overrides)
        session = DatasetSessionContext.get_session(session_id)
        payload = ResultManager.format_dashboard_payload(session)
        return jsonify({
            "success": True,
            "cleaning_result": result,
            "updated_data": payload
        })
    except Exception as e:
        logger.exception("Error executing cleaning operations.")
        return jsonify({"error": str(e)}), 500

@app.route("/api/generate-reports/<session_id>", methods=["POST"])
def generate_reports(session_id: str):
    """Generates PDF, Excel, and cleaned dataset files."""
    try:
        artifacts = agent.export_reports(session_id)
        return jsonify({"success": True, "artifacts": artifacts})
    except Exception as e:
        logger.exception("Error generating reports.")
        return jsonify({"error": str(e)}), 500

@app.route("/api/download/<filename>", methods=["GET"])
def download_artifact(filename: str):
    """Serves generated reports and export datasets securely."""
    safe_name = secure_filename(filename)
    file_path = Config.OUTPUT_FOLDER / safe_name
    if not file_path.exists():
        return jsonify({"error": "Requested file not found or expired."}), 404

    return send_from_directory(
        directory=Config.OUTPUT_FOLDER,
        path=safe_name,
        as_attachment=True
    )

if __name__ == "__main__":
    logger.info(f"Starting DataGuard AI on http://{Config.HOST}:{Config.PORT}")
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
