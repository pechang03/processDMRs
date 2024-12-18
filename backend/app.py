from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

@app.route('/api/health')
def health_check():
    return jsonify({"status": "healthy"})

@app.route('/api/dmr/analysis')
def get_dmr_analysis():
    # Placeholder for DMR analysis endpoint
    return jsonify({
        "results": [
            {"id": 1, "status": "complete", "data": {}}
        ]
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)

