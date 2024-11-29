from flask import Flask
from biclique_analysis.classifier import BicliqueSizeCategory

app = Flask(__name__)

@app.template_filter('sort_by_complexity')
def sort_by_complexity(components):
    """Sort components by complexity category."""
    def get_complexity_score(component):
        category = component.get('category', 'empty').upper()
        try:
            return BicliqueSizeCategory[category].value
        except KeyError:
            return 0
    return sorted(components, key=get_complexity_score, reverse=True)
