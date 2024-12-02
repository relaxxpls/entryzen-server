from flask import Flask, request, jsonify
from flask_cors import CORS
from src.parse_pdf import parse_pdf
from io import BytesIO

app = Flask(__name__)
CORS(app)


@app.route("/upload", methods=["POST"])
def upload():
    try:
        # Check if file is present in request
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]

        # Check if file has a name
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        # Convert FileStorage to BytesIO
        pdf_bytes = BytesIO(file.read())
        pdf_bytes.name = file.filename  # Add filename attribute to BytesIO object

        # Get company name from request
        company_name = request.form.get("company_name")
        if not company_name:
            return jsonify({"error": "No company_name data provided"}), 400

        # Call parse_pdf function with BytesIO object
        primary_series, secondary_df = parse_pdf(company_name, pdf_bytes)

        # Convert to JSON format
        response_data = {
            "primary": primary_series.to_json(),
            "secondary": secondary_df.to_json(),
        }

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=7860)
