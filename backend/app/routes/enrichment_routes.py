from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from ..database import get_db
from ..enrichment.enrichment import get_dmr_enrichment, get_biclique_enrichment

router = APIRouter(prefix="/graph")

@router.get("/go-enrichment-dmr/{timepoint_id}/{biclique_id}")
async def read_dmr_enrichment(
    timepoint_id: int,
    biclique_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get GO enrichment analysis results for DMRs in a biclique
    """
    try:
        results = await get_dmr_enrichment(db, timepoint_id, biclique_id)
        return {"data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/go-enrichment-biclique/{timepoint_id}/{biclique_id}")
async def read_biclique_enrichment(
    timepoint_id: int,
    biclique_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get GO enrichment analysis results for genes in a biclique
    """
    try:
        results = await get_biclique_enrichment(db, timepoint_id, biclique_id)
        return {"data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

