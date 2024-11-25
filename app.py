import argparse
from flask import render_template
from extensions import app
from routes import index_route, statistics_route, component_detail_route
from process_data import process_data

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
    return parser.parse_args()

# Register routes once
app.add_url_rule("/", "index_route", index_route)
app.add_url_rule("/statistics", "statistics_route", statistics_route)
app.add_url_rule(
    "/component/<int:component_id>", "component_detail", component_detail_route
)
app.add_url_rule(
    "/component/<int:component_id>/<type>", "component_detail", component_detail_route
)

def main():
    """Main entry point for the application."""
    args = parse_arguments()
    
    # Store format in app config
    app.config["BICLIQUE_FORMAT"] = args.format
    
    # Run the Flask app
    app.run(debug=args.debug, port=args.port)

if __name__ == "__main__":
    main()
