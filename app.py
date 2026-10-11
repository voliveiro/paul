import os
from datetime import datetime
from docx import Document
from pypdf import PdfReader
from flask import Flask, request, jsonify, Response, send_file, stream_with_context
from flask_cors import CORS
from dotenv import load_dotenv
from agents import AGENTS
from export import build_report
from orchestrator import run_simulation_stream, select_agents

load_dotenv()

app = Flask(__name__, static_folder="frontend")
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20 MB upload limit
CORS(app, expose_headers=["Content-Disposition"])


@app.route("/agents", methods=["GET"])
def get_agents():
    return jsonify([{"id": a.id, "name": a.name, "role": a.role} for a in AGENTS])


@app.route("/select-agents", methods=["POST"])
def select_agents_route():
    data = request.get_json()
    proposal = data.get("proposal", "").strip()
    if not proposal:
        return jsonify({"error": "No proposal provided"}), 400
    selected = select_agents(proposal)
    return jsonify({"agents": selected})


@app.route("/extract", methods=["POST"])
def extract():
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "No file uploaded"}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    try:
        if ext == ".pdf":
            reader = PdfReader(file.stream)
            text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
        elif ext == ".docx":
            doc = Document(file.stream)
            # Walk the body in order so tables stay where they appear
            lines = []
            for block in doc.iter_inner_content():
                if hasattr(block, "rows"):
                    lines += [" | ".join(c.text.strip() for c in row.cells) for row in block.rows]
                else:
                    lines.append(block.text)
            text = "\n".join(lines)
        elif ext in (".txt", ".md"):
            text = file.read().decode("utf-8", errors="replace")
        else:
            return jsonify({"error": f"Unsupported file type: {ext or 'unknown'}. Use PDF, DOCX, TXT or MD."}), 400
    except Exception as e:
        return jsonify({"error": f"Could not read file: {e}"}), 400

    text = text.strip()
    if not text:
        return jsonify({"error": "No text found in document (scanned PDFs are not supported)"}), 400
    return jsonify({"text": text, "filename": file.filename})


@app.route("/export", methods=["POST"])
def export():
    data = request.get_json()
    proposal = data.get("proposal", "").strip()
    responses = data.get("responses", [])
    synthesis = data.get("synthesis", "")
    if not proposal or not responses:
        return jsonify({"error": "Nothing to export — run a simulation first"}), 400

    buf = build_report(proposal, responses, synthesis, data.get("synthesis_mode", "standard"))
    filename = f"paul_simulation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
    return send_file(
        buf,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@app.route("/simulate", methods=["POST"])
def simulate():
    data = request.get_json()
    proposal = data.get("proposal", "").strip()
    selected_ids = data.get("agents", None)
    synthesis_mode = data.get("synthesis_mode", "standard")

    if not proposal:
        return jsonify({"error": "No proposal provided"}), 400

    def generate():
        for event in run_simulation_stream(proposal, selected_ids, synthesis_mode):
            yield event

    response = Response(stream_with_context(generate()), mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    return response


@app.route("/")
def index():
    return app.send_static_file("index.html")


if __name__ == "__main__":
    app.run(debug=True, port=5001, threaded=True)
