from flask import Flask, render_template
from routes import index_route, statistics_route, component_detail_route
from process_data import process_data

app = Flask(__name__)

# Register routes
app.add_url_rule('/', 'index_route', index_route)
app.add_url_rule('/statistics', 'statistics_route', statistics_route)
app.add_url_rule('/component/<int:component_id>', 'component_detail', component_detail_route)

if __name__ == "__main__":
    app.run(debug=True)





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
