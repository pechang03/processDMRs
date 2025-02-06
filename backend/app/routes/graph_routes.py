from flask import jsonify, current_app, Blueprint
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
import time
import networkx as nx
from plotly.utils import PlotlyJSONEncoder

from ..schemas import (
    GraphComponentSchema,
    BicliqueMemberSchema,
)
from ..database.connection import get_db_engine
from ..visualization.vis_components import create_component_visualization
from ..biclique_analysis.edge_classification import classify_edges
from ..visualization.graph_layout_biclique import CircularBicliqueLayout
from ..utils.node_info import NodeInfo
from ..utils.json_utils import convert_plotly_object

graph_bp = Blueprint("graph_routes", __name__, url_prefix="/api/graph")


@graph_bp.route("/<int:timepoint_id>/<int:component_id>", methods=["GET"])
