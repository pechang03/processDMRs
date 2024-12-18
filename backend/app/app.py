from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/api/health')
def health_check():
    return jsonify({"status": "running"}), 200

if __name__ == '__main__':
    app.run(debug=True)
