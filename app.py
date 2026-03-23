from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from dotenv import load_dotenv
from agents import AGENTS
from orchestrator import run_simulation_stream, select_agents

load_dotenv()

app = Flask(__name__, static_folder="frontend")
CORS(app)


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


@app.route("/simulate", methods=["POST"])
def simulate():
    data = request.get_json()
    proposal = data.get("proposal", "").strip()
    selected_ids = data.get("agents", None)

    if not proposal:
        return jsonify({"error": "No proposal provided"}), 400

    def generate():
        for event in run_simulation_stream(proposal, selected_ids):
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
