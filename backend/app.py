from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BASE = Path(__file__).resolve().parent
FRONTEND = BASE.parent / "frontend"


@app.route("/")
def index():
    return send_from_directory(str(FRONTEND), "index.html")


@app.route("/style.css")
def stylesheet():
    return send_from_directory(str(FRONTEND), "style.css")


@app.route("/app.js")
def javascript():
    return send_from_directory(str(FRONTEND), "app.js")


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/glacier/<int:year>")
def glacier(year):
    if not 2017 <= year <= 2024:
        return jsonify({
            "error": "Year must be between 2017 and 2024."
        }), 400

    glacier_id = request.args.get("glacier", "rob-roy").strip().lower()

    if glacier_id not in ("rob-roy", "marmolada"):
        return jsonify({
            "error": "Glacier must be rob-roy or marmolada."
        }), 400

    try:
        if glacier_id == "marmolada":
            from marmolada_analysis import calculate_glacier

            name = "Marmolada"
            centre = [11.857975, 46.43522]
        else:
            from glacier_analysis import calculate_glacier

            name = "Rob Roy"
            centre = [168.741, -44.455]

        result = dict(calculate_glacier(year))
        result.update({
            "glacierId": glacier_id,
            "glacier": name,
            "studyCentre": centre,
            "areaUnit": "km2",
        })

        return jsonify(result)

    except Exception:
        app.logger.exception("Glacier analysis failed")
        return jsonify({
            "error": "Glacier analysis failed. Please try again.",
            "glacierId": glacier_id,
            "year": year,
        }), 500


if __name__ == "__main__":
    app.run(port=5000)
