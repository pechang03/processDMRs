"""Database operations for dominating sets."""

from typing import Set, Dict, Tuple
import networkx as nx
import pandas as pd
from sqlalchemy.orm import Session
from .models import DominatingSet
from backend.app.core.rb_domination import greedy_rb_domination

def store_dominating_set(
    session: Session,
    timepoint_id: int,
    dominating_set: Set[int],
    area_stats: Dict[int, float],
    utility_scores: Dict[int, float],
    dominated_counts: Dict[int, int]
):
    """Store a computed dominating set in the database."""
    # First remove any existing entries for this timepoint
    session.query(DominatingSet).filter_by(timepoint_id=timepoint_id).delete()
    
    # Add new entries
    for dmr_id in dominating_set:
        ds_entry = DominatingSet(
            timepoint_id=timepoint_id,
            dmr_id=dmr_id,
            area_stat=area_stats.get(dmr_id),
            utility_score=utility_scores.get(dmr_id),
            dominated_gene_count=dominated_counts.get(dmr_id)
        )
        session.add(ds_entry)
    
    session.commit()

def get_dominating_set(
    session: Session,
    timepoint_id: int
) -> Tuple[Set[int], Dict[str, Dict]]:
    """Retrieve the dominating set for a timepoint."""
    entries = session.query(DominatingSet).filter_by(timepoint_id=timepoint_id).all()
    
    if not entries:
        return None, None
        
    dominating_set = {entry.dmr_id for entry in entries}
    metadata = {
        'area_stats': {entry.dmr_id: entry.area_stat for entry in entries},
        'utility_scores': {entry.dmr_id: entry.utility_score for entry in entries},
        'dominated_counts': {entry.dmr_id: entry.dominated_gene_count for entry in entries},
        'calculation_timestamp': min(entry.calculation_timestamp for entry in entries)
    }
    
    return dominating_set, metadata
