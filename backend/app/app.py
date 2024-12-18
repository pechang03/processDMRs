from flask import jsonify
import os
from app.utils.extensions import app
from dotenv import load_dotenv

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

def configure_app(app):
    # Look for processDMR.env in current and parent directories
    env_file = "processDMR.env"
    env_paths = [
        env_file,
        os.path.join("..", env_file),
        os.path.join("..", "..", env_file)
    ]
    
    env_loaded = False
    for path in env_paths:
        if os.path.exists(path):
            load_dotenv(path)
            print(f"Loaded environment from {path}")
            env_loaded = True
            break
    
    if not env_loaded:
        print("Warning: processDMR.env not found")

    # Set default configuration with specific database name
    app.config.setdefault("DATABASE_URL", "sqlite:///dmr_analysis.db")
    app.config.setdefault("FLASK_ENV", "development")

    # Override with environment variables if they exist
    app.config["DATABASE_URL"] = os.getenv("DATABASE_URL", app.config["DATABASE_URL"])
    app.config["FLASK_ENV"] = os.getenv("FLASK_ENV", app.config["FLASK_ENV"])
    
    # Add MIME type handling
    app.config["MIME_TYPES"] = {".css": "text/css", ".js": "application/javascript"}
    
    # Print the configuration being used
    print(f"Using database: {app.config['DATABASE_URL']}")
    print(f"Environment: {app.config['FLASK_ENV']}")
    
    return env_loaded

if __name__ == '__main__':
    configure_app(app)
    port = int(os.environ.get('FLASK_PORT', 5555))
    app.run(host='0.0.0.0', port=port, debug=True)
