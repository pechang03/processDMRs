from flask import Blueprint, jsonify, current_app
from typing import List, Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database.models import EdgeDetails, Gene
from ..database.connection import get_db_engine

edge_bp = Blueprint('edge_routes', __name__)

@edge_bp.route("/timepoint/<int:timepoint_id>/dmr/<int:dmr_id>")
def get_dmr_edge_details(timepoint_id: int, dmr_id: int):
    """Get edge details for a specific DMR in a timepoint."""
    try:
        engine = get_db_engine()
        with Session(engine) as db:
            edges = db.query(EdgeDetails).filter(
                EdgeDetails.timepoint_id == timepoint_id,
                EdgeDetails.dmr_id == dmr_id
            ).all()

            if not edges:
                return jsonify({"status": "error", "message": "No edge details found"}), 404

            result = []
            for edge in edges:
                gene = db.get(Gene, edge.gene_id)
                result.append({
                    "dmr_id": edge.dmr_id,
                    "gene_id": edge.gene_id,
                    "gene_symbol": gene.symbol if gene else None,
                    "edge_type": edge.edge_type,
                    "edit_type": edge.edit_type,
                    "distance_from_tss": edge.distance_from_tss,
                    "description": edge.description
                })

            return jsonify({"status": "success", "edges": result})

    except Exception as e:
        current_app.logger.error(f"Error getting DMR edge details: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@edge_bp.route("/timepoint/<int:timepoint_id>/gene/<int:gene_id>")
def get_gene_edge_details(timepoint_id: int, gene_id: int):
    """Get edge details for a specific gene in a timepoint."""
    try:
        engine = get_db_engine()
        with Session(engine) as db:
            edges = db.query(EdgeDetails).filter(
                EdgeDetails.timepoint_id == timepoint_id,
                EdgeDetails.gene_id == gene_id
            ).all()

            if not edges:
                return jsonify({"status": "error", "message": "No edge details found"}), 404

            result = []
            for edge in edges:
                gene = db.get(Gene, edge.gene_id)
                result.append({
                    "dmr_id": edge.dmr_id,
                    "gene_id": edge.gene_id,
                    "gene_symbol": gene.symbol if gene else None,
                    "edge_type": edge.edge_type,
                    "edit_type": edge.edit_type,
                    "distance_from_tss": edge.distance_from_tss,
                    "description": edge.description
                })

            return jsonify({"status": "success", "edges": result})

    except Exception as e:
        current_app.logger.error(f"Error getting gene edge details: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

