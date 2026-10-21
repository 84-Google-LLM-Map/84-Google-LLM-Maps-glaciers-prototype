from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
import ee

from flask_cors import CORS
from glacier_analysis import calculate_automatic_reference_glacier

from glaciers import GLACIERS

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

    # -----------------------------------------------------
    # VALIDATE YEAR
    # -----------------------------------------------------

    if not 2017 <= year <= 2024:
        return jsonify({
            "error": "Year must be between 2017 and 2024."
        }), 400


    # -----------------------------------------------------
    # GET SELECTED GLACIER
    # -----------------------------------------------------

    glacier_id = (
        request.args
        .get("glacier", "rob-roy")
        .strip()
        .lower()
    )


    # -----------------------------------------------------
    # VALIDATE GLACIER
    # -----------------------------------------------------

    # Marmolada remains separate because it still uses
    # the provisional demo analysis.
    valid_glaciers = list(GLACIERS.keys()) + ["marmolada"]

    if glacier_id not in valid_glaciers:
        return jsonify({
            "error": (
                f"Unknown glacier '{glacier_id}'. "
                f"Available glaciers: {', '.join(valid_glaciers)}"
            )
        }), 400


    try:

        # -------------------------------------------------
        # MARMOLADA
        # -------------------------------------------------

        if glacier_id == "marmolada":

            from marmolada_analysis import calculate_glacier

            result = dict(
                calculate_glacier(year)
            )

            # Ensure frontend receives the selected ID
            result["glacierId"] = glacier_id


        # -------------------------------------------------
        # ALL MANUALLY REFERENCED GLACIERS
        # -------------------------------------------------

        else:

            from glacier_analysis import calculate_glacier

            result = dict(
                calculate_glacier(
                    glacier_id,
                    year
                )
            )


        # -------------------------------------------------
        # RETURN RESULT
        # -------------------------------------------------

        return jsonify(result)


    except Exception as exc:

        app.logger.exception(
            "Glacier analysis failed"
        )

        return jsonify({
            "error": "Glacier analysis failed. Please try again.",
            "glacierId": glacier_id,
            "year": year
        }), 500


@app.route("/api/automatic-reference-analysis", methods=["POST"])
def automatic_reference_analysis():
    try:
        data = request.get_json() or {}

        geometry = data.get("geometry")
        year = int(data.get("year", 2019))

        if not geometry:
            return jsonify({
                "error": "No study area was provided."
            }), 400

        if not 2017 <= year <= 2024:
            return jsonify({
                "error": "Year must be between 2017 and 2024."
            }), 400

        study_area = ee.Geometry(geometry)

        result = calculate_automatic_reference_glacier(
            year,
            study_area
        )

        return jsonify(result)

    except Exception as exc:

        app.logger.exception(
            "Automatic reference analysis failed"
        )

        return jsonify({
            "error": str(exc)
        }), 500
    
if __name__ == "__main__":
    app.run(
        debug=True,
        port=5000
    )
