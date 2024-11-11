"""Layout creation functionality"""

def create_plot_layout() -> dict:
    """Create the plot layout configuration."""
    return {
        "showlegend": True,
        "hovermode": "closest",
        "margin": dict(b=40, l=40, r=40, t=40),
        "xaxis": dict(showgrid=False, zeroline=False, showticklabels=False),
        "yaxis": dict(showgrid=False, zeroline=False, showticklabels=False),
    }
