from flask import Flask, jsonify
from flask_cors import CORS

from marmolada_analysis import calculate_glacier

app = Flask(__name__)
CORS(app)


@app.route("/api/glacier/<int:year>")
def glacier(year):

    if year < 2017 or year > 2024:
        return jsonify({
            "error": "Year must be between 2017 and 2024"
        }), 400

    try:
        result = calculate_glacier(year)

        return jsonify(result)

    except Exception as e:

        print("Earth Engine error:", e)

        return jsonify({
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(
        debug=True,
        port=5000
    )
