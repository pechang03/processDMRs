import argparse
import sys
from flask import Flask, render_template
from routes import index_route, statistics_route, component_detail_route
from process_data import process_data

app = Flask(__name__)

# Add version constant at top of file
__version__ = "1.0.0"

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="DMR Analysis Web Application",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port to run the web server on'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Run in debug mode'
    )
    parser.add_argument(
        '--format',
        choices=['gene-name', 'number'],
        default='gene-name',
        help='Format for biclique file parsing (gene-name or number)'
    )
    return parser.parse_args()

# Register routes
app.add_url_rule('/', 'index_route', index_route)
app.add_url_rule('/statistics', 'statistics_route', statistics_route)
app.add_url_rule('/component/<int:component_id>', 'component_detail', component_detail_route)

if __name__ == "__main__":
    args = parse_arguments()
    # Store format in app config so it's accessible to the processing functions
    app.config['BICLIQUE_FORMAT'] = args.format
    app.run(debug=args.debug, port=args.port)





@app.route("/statistics")
def statistics():
    try:
        results = process_data()
        if "error" in results:
            return render_template("error.html", message=results["error"])

        # Calculate additional statistics if needed
        detailed_stats = {
            "size_distribution": results.get("size_distribution", {}),
            "coverage": results.get("coverage", {}),
            "node_participation": results.get("node_participation", {}),
            "edge_coverage": results.get("edge_coverage", {}),
        }

        return render_template(
            "statistics.html", statistics=detailed_stats, bicliques_result=results
        )
    except Exception as e:
        return render_template("error.html", message=str(e))


from flask import Flask
from routes import index_route, statistics_route, component_detail_route

app = Flask(__name__)

# Register routes
app.add_url_rule('/', 'index_route', index_route)
app.add_url_rule('/statistics', 'statistics_route', statistics_route)
app.add_url_rule('/component/<int:component_id>', 'component_detail', component_detail_route)

if __name__ == "__main__":
    app.run(debug=True)
