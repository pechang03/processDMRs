from fastapi import APIRouter, HTTPException, Depends
from typing import List
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import EdgeDetails, Gene
from ..database.connection import get_async_session

router = APIRouter(prefix="/api/graph/edge-details", tags=["edges"])

class EdgeDetailBase(BaseModel):
    dmr_id: int
    gene_id: int
    gene_symbol: str | None
    edge_type: str
    edit_type: str
    distance_from_tss: int
    description: str | None

    class Config:
        orm_mode = True

class EdgeDetailsResponse(BaseModel):
    edges: List[EdgeDetailBase]

@router.get("/timepoint/{timepoint_id}/dmr/{dmr_id}", 
        response_model=EdgeDetailsResponse)
async def get_dmr_edge_details(
    timepoint_id: int,
    dmr_id: int,
    db: AsyncSession = Depends(get_async_session)
) -> EdgeDetailsResponse:
    """Get edge details for a specific DMR in a timepoint."""
    try:
        edges = (
            await db.scalars(
                select(EdgeDetails)
                .filter(
                    EdgeDetails.timepoint_id == timepoint_id,
                    EdgeDetails.dmr_id == dmr_id
                )
            )
        ).all()

        if not edges:
            raise HTTPException(status_code=404, detail="No edge details found")

        result = []
        for edge in edges:
            gene = await db.get(Gene, edge.gene_id)
            result.append(
                EdgeDetailBase(
                    dmr_id=edge.dmr_id,
                    gene_id=edge.gene_id,
                    gene_symbol=gene.symbol if gene else None,
                    edge_type=edge.edge_type,
                    edit_type=edge.edit_type,
                    distance_from_tss=edge.distance_from_tss,
                    description=edge.description
                )
            )

        return EdgeDetailsResponse(edges=result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/timepoint/{timepoint_id}/gene/{gene_id}",
        response_model=EdgeDetailsResponse)
async def get_gene_edge_details(
    timepoint_id: int,
    gene_id: int,
    db: AsyncSession = Depends(get_async_session)
) -> EdgeDetailsResponse:
    """Get edge details for a specific gene in a timepoint."""
    try:
        edges = (
            await db.scalars(
                select(EdgeDetails)
                .filter(
                    EdgeDetails.timepoint_id == timepoint_id,
                    EdgeDetails.gene_id == gene_id
                )
            )
        ).all()

        if not edges:
            raise HTTPException(status_code=404, detail="No edge details found")

        result = []
        for edge in edges:
            result.append(
                EdgeDetailBase(
                    dmr_id=edge.dmr_id,
                    gene_id=edge.gene_id,
                    gene_symbol=(await db.get(Gene, edge.gene_id)).symbol,
                    edge_type=edge.edge_type,
                    edit_type=edge.edit_type,
                    distance_from_tss=edge.distance_from_tss,
                    description=edge.description
                )
            )

        return EdgeDetailsResponse(edges=result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

