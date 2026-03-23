from flask import Flask, request, jsonify
from flask_cors import cross_origin
from dotenv import load_dotenv
from orchestrator import run_simulation

load_dotenv()

app = Flask(__name__, static_folder="frontend")


@app.route("/simulate", methods=["POST"])
@cross_origin()
def simulate():
    data = request.get_json()
    proposal = data.get("proposal", "").strip()

    if not proposal:
        return jsonify({"error": "No proposal provided"}), 400

    result = run_simulation(proposal)
    return jsonify(result)


@app.route("/")
def index():
    return app.send_static_file("index.html")


if __name__ == "__main__":
    app.run(debug=True, port=5001)