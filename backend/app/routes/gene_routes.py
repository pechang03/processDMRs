from flask import Blueprint, jsonify, current_app
from sqlalchemy.orm import Session
from ..database.connection import get_db_engine
from ..database.models import GeneDetails

gene_bp = Blueprint("gene_routes", __name__, url_prefix="/api/genes")

@gene_bp.route("/details/<int:gene_id>", methods=["GET"])
def get_gene_details(gene_id: int):
    """Get detailed information for a specific gene."""
    try:
        engine = get_db_engine()
        with Session(engine) as session:
            details = session.query(GeneDetails).filter_by(gene_id=gene_id).first()
            
            if not details:
                return jsonify({"error": "Gene details not found", "status": 404}), 404
            
            return jsonify({
                "gene_id": details.gene_id,
                "NCBI_id": details.NCBI_id,
                "annotations": details.annotations
            })
            
    except Exception as e:
        current_app.logger.error(f"Error retrieving gene details: {str(e)}")
        return jsonify({"error": "Internal server error", "status": 500}), 500
