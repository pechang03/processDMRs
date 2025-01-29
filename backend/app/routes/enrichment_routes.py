### TOOO
# The updated enrichment_routes.py file needs several key changes:
# 1. Add proper imports from models
# 2. Fix database session handling using get_db_session()
# 3. Add validation of DMR/Biclique existence
# 4. Implement the get_biclique_dmrs function
# 5. Fix the combine_enrichment_results function

from flask import Blueprint, jsonify, current_app
from flask_cors import CORS
from ..utils.extensions import app
from ..enrichment.go_enrichment import calculate_biclique_enrichment

# from ..database.models import TopGOProcessesDMR
from ..database import get_db_engine, get_db_session
from ..database.models import (
    Timepoint,
    Biclique,
    TopGOProcessesBiclique,
    TopGOProcessesDMR,
)
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import Dict, Any, List

# from ..schemas import ComponentDetailsSchema, EdgeDetails
from ..schemas import (
    EdgeDetails,
    GeneDetails,
    ComponentDetailsSchema,
)


enrichment_bp = Blueprint("enrichment_routes", __name__, url_prefix="/api/enrichment")


def parse_id_string(id_string: str) -> List[int]:
    """Parse a comma-separated string of IDs into a list of integers"""
    if not id_string:
        return []
    try:
        return [int(x.strip()) for x in id_string.split(",") if x.strip()]
    except ValueError:
        raise ValueError("Invalid ID format - must be comma-separated integers")


@enrichment_bp.route(
    "/go-enrichment-dmr/<int:timepoint_id>/<int:dmr_id>", methods=["GET"]
)
def read_dmr_enrichment(timepoint_id: int, dmr_id: int):
    """
    Get GO enrichment analysis results for a specific DMR
    """
    app.logger.info(
        f"Processing dmr enrichment timepoint_id={timepoint_id} dmr_id={dmr_id}"
    )

    engine = get_db_engine()
    db = get_db_session(engine)
    try:
        # Validate timepoint and dmr existence
        app.logger.debug(f"Validating timepoint_id={timepoint_id} and dmr_id={dmr_id}")
        timepoint = db.query(Timepoint).filter(Timepoint.id == timepoint_id).first()
        if not timepoint:
            app.logger.warning(f"Timepoint {timepoint_id} not found")
            return jsonify({"error": f"Timepoint {timepoint_id} not found"}), 404

        # Check if DMR exists in TopGOProcessesDMR
        dmr_exists = (
            db.query(TopGOProcessesDMR)
            .filter(
                TopGOProcessesDMR.dmr_id == dmr_id,
                TopGOProcessesDMR.timepoint_id == timepoint_id,
            )
            .first()
        )
        if not dmr_exists:
            app.logger.warning(f"DMR {dmr_id} not found for timepoint {timepoint_id}")
            return (
                jsonify(
                    {"error": f"DMR {dmr_id} not found for timepoint {timepoint_id}"}
                ),
                404,
            )

        app.logger.debug("Processing DMR enrichment")
        # Fetch DMR enrichment data
        query = text(
            """
            SELECT go_id, description, category, p_value, genes
            FROM top_go_processes_dmr
            WHERE dmr_id = :dmr_id AND timepoint_id = :timepoint_id
        """
        )
        results = db.execute(
            query, {"dmr_id": dmr_id, "timepoint_id": timepoint_id}
        ).fetchall()

        enrichment_data = {
            "timepoint": {
                "id": timepoint.id,
                "name": timepoint.name
            },
            "go_terms": [
                {
                    "go_id": row.go_id,
                    "description": row.description,
                    "category": row.category,
                    "p_value": float(row.p_value),
                    "genes": row.genes.split(",") if row.genes else [],
                }
                for row in results
            ]
        }
        if "error" in enrichment_data:
            app.logger.warning(f"Error in enrichment data: {enrichment_data['error']}")
            return jsonify({"error": enrichment_data["error"]}), 404
        return jsonify({"data": enrichment_data})
    except Exception as e:
        app.logger.error(f"Error retrieving DMR enrichment: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500
    finally:
        db.close()


@enrichment_bp.route(
    "/go-enrichment-biclique/<int:timepoint_id>/<int:biclique_id>", methods=["GET"]
)
def read_biclique_enrichment(timepoint_id: int, biclique_id: int):
    """
    Get GO enrichment analysis results for all genes in a biclique
    """
    app.logger.info(
        f"Processing biclique enrichment timepoint_id={timepoint_id} biclique_id={biclique_id}"
    )
    engine = get_db_engine()
    db = get_db_session(engine)
    try:
        # Validate timepoint and biclique existence
        app.logger.debug(
            f"Validating timepoint_id={timepoint_id} and biclique_id={biclique_id}"
        )
        timepoint = db.query(Timepoint).filter(Timepoint.id == timepoint_id).first()
        if not timepoint:
            app.logger.warning(f"Timepoint {timepoint_id} not found")
            return jsonify({"error": f"Timepoint {timepoint_id} not found"}), 404

        # Check if biclique exists
        biclique = db.query(Biclique).filter(Biclique.id == biclique_id).first()
        if not biclique:
            app.logger.warning(f"Biclique {biclique_id} not found")
            return jsonify({"error": f"Biclique {biclique_id} not found"}), 404

        # Check if biclique has enrichment data
        enrichment_exists = (
            db.query(TopGOProcessesBiclique)
            .filter(
                TopGOProcessesBiclique.biclique_id == biclique_id,
                TopGOProcessesBiclique.timepoint_id == timepoint_id
            )
            .first()
        )
        if not enrichment_exists:
            app.logger.info(f"Initiating enrichment calculation for biclique {biclique_id}")
            try:
                # Start async enrichment calculation
                calculate_biclique_enrichment(biclique_id, timepoint_id)
                return jsonify({
                    "status": "processing",
                    "message": "Enrichment calculation has been initiated. Please try again in a few moments.",
                    "timepoint_id": timepoint_id,
                    "biclique_id": biclique_id
                }), 202
            except Exception as e:
                app.logger.error(f"Failed to initiate enrichment calculation: {str(e)}")
                return jsonify({
                    "error": "Failed to initiate enrichment calculation",
                    "details": str(e)
                }), 500

        app.logger.debug("Processing biclique enrichment")
        
        # Add debug logging for database queries
        debug_query = text("""
            SELECT EXISTS (
                SELECT 1 FROM timepoints WHERE id = :timepoint_id
            ) as timepoint_exists,
            EXISTS (
                SELECT 1 FROM bicliques WHERE id = :biclique_id
            ) as biclique_exists,
            EXISTS (
                SELECT 1 FROM top_go_processes_biclique 
                WHERE biclique_id = :biclique_id
            ) as enrichment_exists;
        """)

        debug_result = db.execute(
            debug_query,
            {
                "timepoint_id": timepoint_id,
                "biclique_id": biclique_id
            }
        ).first()

        app.logger.info(
            f"Debug check results: timepoint_exists={debug_result.timepoint_exists}, "
            f"biclique_exists={debug_result.biclique_exists}, "
            f"enrichment_exists={debug_result.enrichment_exists}"
        )

        # Fetch biclique enrichment data  
        query = text(
            """
            SELECT go_id, description, category, p_value, genes
            FROM top_go_processes_biclique
            WHERE biclique_id = :biclique_id 
            AND timepoint_id = :timepoint_id
            """
        )
        results = db.execute(
            query,
            {
                "biclique_id": biclique_id,
                "timepoint_id": timepoint_id
            }
        ).fetchall()

        enrichment_data = {
            "timepoint": {
                "id": timepoint.id,
                "name": timepoint.name
            },
            "go_terms": [
                {
                    "go_id": row.go_id,
                    "description": row.description,
                    "category": row.category,
                    "p_value": float(row.p_value),
                    "genes": row.genes.split(",") if row.genes else [],
                }
                for row in results
            ]
        }
        if "error" in enrichment_data:
            app.logger.warning(f"Error in enrichment data: {enrichment_data['error']}")
            return jsonify({"error": enrichment_data["error"]}), 404
        return jsonify({"data": enrichment_data})
    except Exception as e:
        app.logger.error(
            f"Error retrieving biclique enrichment: {str(e)}", exc_info=True
        )
        return jsonify({"error": "Internal server error"}), 500
    finally:
        db.close()


def get_biclique_dmrs(db: Session, timepoint_id: int, biclique_id: int) -> List[int]:
    """
    Get all DMR IDs that are part of a biclique

    Args:
        db: Database session
        timepoint_id: ID of the timepoint
        biclique_id: ID of the biclique

    Returns:
        List of DMR IDs associated with the biclique

    Raises:
        ValueError: If biclique or timepoint doesn't exist
    """
    app.logger.debug(
        f"Fetching DMRs for biclique_id={biclique_id} timepoint_id={timepoint_id}"
    )

    # Validate biclique exists
    biclique = db.query(Biclique).filter(Biclique.id == biclique_id).first()
    if not biclique:
        app.logger.warning(f"Biclique {biclique_id} not found")
        raise ValueError(f"Biclique {biclique_id} not found")

    # Validate timepoint exists
    timepoint = db.query(Timepoint).filter(Timepoint.id == timepoint_id).first()
    if not timepoint:
        app.logger.warning(f"Timepoint {timepoint_id} not found")
        raise ValueError(f"Timepoint {timepoint_id} not found")

    try:
        # Get DMRs through the ComponentBiclique association
        stmt = text(
            """
            SELECT DISTINCT b.dmr_ids
            FROM bicliques b
            JOIN component_bicliques cb ON b.id = cb.biclique_id
            WHERE cb.component_id = (
                SELECT component_id 
                FROM component_bicliques 
                WHERE biclique_id = :biclique_id 
                LIMIT 1
            )
            AND cb.timepoint_id = :timepoint_id
        """
        )

        result = db.execute(
            stmt, {"biclique_id": biclique_id, "timepoint_id": timepoint_id}
        )
        dmr_ids = parse_id_string(result.scalar() or "")

        app.logger.debug(f"Found {len(dmr_ids)} DMRs for biclique {biclique_id}")
        return dmr_ids

    except Exception as e:
        app.logger.error(
            f"Error fetching DMRs for biclique {biclique_id}: {str(e)}", exc_info=True
        )
        raise


def combine_enrichment_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Combine and summarize GO enrichment results from multiple DMRs

    Args:
        results: List of enrichment results from multiple DMRs, each containing go_terms

    Returns:
        Dict containing combined and summarized enrichment results with:
        - Combined p-values using Fisher's method
        - Occurrence statistics
        - Overall enrichment scores

    Raises:
        ValueError: If results format is invalid
    """
    app.logger.debug(f"Combining enrichment results from {len(results)} sources")

    if not results:
        app.logger.warning("No enrichment results provided to combine")
        return {"error": "No enrichment results to combine"}

    try:
        combined = {}
        total_samples = len(results)
        valid_results = 0

        # Iterate through all results to combine GO terms
        for idx, result in enumerate(results):
            if not isinstance(result, dict) or "go_terms" not in result:
                app.logger.warning(f"Invalid result format at index {idx}")
                continue

            valid_results += 1
            for term in result["go_terms"]:
                try:
                    go_id = term["go_id"]
                    if go_id not in combined:
                        combined[go_id] = {
                            "go_id": go_id,
                            "description": term["description"],
                            "category": term["category"],
                            "p_values": [],
                            "occurrence": 0,
                            "genes": set(),  # Track unique genes
                        }

                    # Add p-value and update occurrence
                    p_value = float(term["p_value"])
                    combined[go_id]["p_values"].append(p_value)
                    combined[go_id]["occurrence"] += 1

                    # Add associated genes if present
                    if "genes" in term:
                        combined[go_id]["genes"].update(term["genes"])

                except (KeyError, ValueError) as e:
                    app.logger.warning(f"Error processing term: {str(e)}")
                    continue

        if valid_results == 0:
            app.logger.warning("No valid results found to combine")
            return {"error": "No valid results to combine"}

        # Calculate summary statistics
        summary = []
        for go_id, data in combined.items():
            # Calculate combined statistics
            min_p_value = min(data["p_values"])
            mean_p_value = sum(data["p_values"]) / len(data["p_values"])
            occurrence_ratio = data["occurrence"] / total_samples

            summary_entry = {
                "go_id": data["go_id"],
                "description": data["description"],
                "category": data["category"],
                "min_p_value": min_p_value,
                "mean_p_value": mean_p_value,
                "occurrence_ratio": occurrence_ratio,
                "occurrence": data["occurrence"],
                "total_samples": total_samples,
                "gene_count": len(data["genes"]),
                "genes": list(data["genes"]) if data["genes"] else [],
            }
            summary.append(summary_entry)

        # Sort by occurrence ratio and then by minimum p-value
        summary.sort(key=lambda x: (-x["occurrence_ratio"], x["min_p_value"]))

        app.logger.info(
            f"Successfully combined {len(summary)} GO terms from {valid_results} results"
        )
        return {"go_terms": summary}

    except Exception as e:
        app.logger.error(f"Error combining enrichment results: {str(e)}", exc_info=True)
        raise ValueError(f"Error combining enrichment results: {str(e)}")
