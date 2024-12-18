from flask import jsonify
import os
from app.utils.extensions import app

@app.route('/')
def root():
    return jsonify({"message": "DMR Analysis API"}), 200

@app.route('/api/health')
def health_check():
    return jsonify({"status": "running"}), 200

# Add basic error handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('FLASK_PORT', 5555))
    app.run(host='0.0.0.0', port=port, debug=True)
