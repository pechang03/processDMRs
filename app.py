import argparse
import os
from extensions import app
from routes import register_blueprints  # Import from routes instead of utils
from process_data import process_data
from utils.constants import DSS1_FILE, DSS_PAIRWISE_FILE
from data_loader import get_excel_sheets

# Version constant
__version__ = "0.0.1-alpha"

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="DMR Analysis Web Application",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "--port", type=int, default=5000, help="Port to run the web server on"
    )
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    parser.add_argument(
        "--format",
        choices=["gene-name", "number"],
        default="gene-name",
        help="Format for biclique file parsing (gene-name or number)",
    )
    parser.add_argument(
        "--data-dir",
        default="./data",
        help="Directory containing DSS1.xlsx and DSS_PAIRWISE.xlsx"
    )
    return parser.parse_args()

def validate_data_files(data_dir: str) -> bool:
    """Validate that required data files exist."""
    dss1_path = os.path.join(data_dir, "DSS1.xlsx")
    pairwise_path = os.path.join(data_dir, "DSS_PAIRWISE.xlsx")
    
    files_exist = True
    if not os.path.exists(dss1_path):
        print(f"Error: DSS1.xlsx not found in {data_dir}")
        files_exist = False
    if not os.path.exists(pairwise_path):
        print(f"Error: DSS_PAIRWISE.xlsx not found in {data_dir}")
        files_exist = False
        
    return files_exist

def configure_data_paths(data_dir: str):
    """Configure data file paths in the application."""
    global DSS1_FILE, DSS_PAIRWISE_FILE
    DSS1_FILE = os.path.join(data_dir, "DSS1.xlsx")
    DSS_PAIRWISE_FILE = os.path.join(data_dir, "DSS_PAIRWISE.xlsx")
    
    app.config["DSS1_FILE"] = DSS1_FILE
    app.config["DSS_PAIRWISE_FILE"] = DSS_PAIRWISE_FILE
    app.config["DATA_DIR"] = data_dir

def main():
    """Main entry point for the application."""
    args = parse_arguments()
    
    # Validate and configure data paths
    if not validate_data_files(args.data_dir):
        print("Error: Required data files not found. Please check your data directory.")
        return 1
        
    # Configure data paths
    configure_data_paths(args.data_dir)
    
    # Store format in app config
    app.config["BICLIQUE_FORMAT"] = args.format
    
    # Register blueprints
    register_blueprints(app)
    
    # Run the Flask app
    app.run(debug=args.debug, port=args.port)
    return 0

if __name__ == "__main__":
    exit(main())
