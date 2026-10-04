from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


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

    except Exception as exc:
        app.logger.exception("Glacier analysis failed")
        return jsonify({
            "error": str(exc),
            "glacierId": glacier_id,
            "year": year,
        }), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
