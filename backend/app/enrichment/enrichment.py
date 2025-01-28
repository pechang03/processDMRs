from sqlalchemy.orm import Session
from sqlalchemy import select, Table, MetaData
from typing import List, Dict, Any
import requests
import json
from ..schemas import (
    GeneDetails, 
    GoEnrichmentBiclique,
    TopGoProcessesBiclique
)
from ..database.models import Biclique

def get_biclique_genes(db: Session, biclique_id: int, timepoint_id: int) -> List[int]:
    """Get all gene IDs in a biclique"""
    query = select(Biclique).where(
        Biclique.id == biclique_id,
        Biclique.timepoint_id == timepoint_id
    )
    result = db.execute(query).first()
    
    if result and result.gene_ids:
        # gene_ids is stored as a JSON array
        return json.loads(result.gene_ids) if isinstance(result.gene_ids, str) else result.gene_ids
    return []

def get_gene_ncbi_ids(db: Session, gene_ids: List[int]) -> Dict[int, str]:
    """
    Get NCBI IDs for a list of genes
    Returns: Dictionary mapping gene_id to NCBI_id
    """
    query = select(GeneDetails.gene_id, GeneDetails.NCBI_id).where(
        GeneDetails.gene_id.in_(gene_ids)
    )
    result = db.execute(query)
    return {row.gene_id: row.NCBI_id for row in result if row.NCBI_id is not None}

def get_stored_biclique_enrichment(db: Session, biclique_id: int, timepoint_id: int) -> Dict[str, Any]:
    """Get stored GO enrichment data for a biclique if it exists"""
    query = select(GoEnrichmentBiclique).where(
        GoEnrichmentBiclique.biclique_id == biclique_id,
        GoEnrichmentBiclique.timepoint_id == timepoint_id
    )
    result = db.execute(query).first()
    
    if result:
        # Get top processes
        top_processes = db.execute(
            select(TopGoProcessesBiclique).where(
                TopGoProcessesBiclique.biclique_id == biclique_id,
                TopGoProcessesBiclique.timepoint_id == timepoint_id
            )
        ).fetchall()
        
        return {
            "go_terms": result.go_terms,
            "p_value": float(result.p_value),
            "enrichment_score": float(result.enrichment_score),
            "source": result.source,
            "biological_process_count": result.biologicalProcessCount,
            "significant_processes": result.significantBiologicalProcesses,
            "top_process": result.topBiologicalProcess,
            "process_details": result.biologicalProcessAnnotationDetails,
            "top_processes": [
                {
                    "term_id": p.termId,
                    "p_value": float(p.pValue),
                    "enrichment_score": float(p.enrichmentScore)
                }
                for p in top_processes
            ]
        }
    return None

def fetch_david_enrichment(ncbi_ids: List[str]) -> Dict[str, Any]:
    """
    Fetch GO enrichment data from DAVID API
    
    Args:
        ncbi_ids: List of NCBI gene IDs
    
    Returns:
        Dictionary containing enrichment results
    """
    # DAVID API endpoint
    api_url = "https://david.ncifcrf.gov/api.jsp"
    
    try:
        # Convert NCBI IDs to DAVID format
        gene_list = ','.join(ncbi_ids)
        
        # Make API request
        params = {
            'type': 'GENE_ID',
            'ids': gene_list,
            'tool': 'chartReport',
            'annot': 'GOTERM_BP_ALL'  # Biological Process GO terms
        }
        
        response = requests.post(api_url, data=params)
        response.raise_for_status()
        
        # Process DAVID response
        enrichment_data = response.json()
        
        # Transform DAVID response to our format
        processed_data = {
            "go_terms": {},
            "top_processes": [],
            "significant_processes": [],
            "process_details": {}
        }
        
        # Process each term
        for term in enrichment_data.get('terms', []):
            processed_data["go_terms"][term['id']] = {
                "name": term['name'],
                "p_value": term['pvalue'],
                "fold_enrichment": term['foldEnrichment'],
                "gene_count": term['geneCount']
            }
            
            # Add to top processes if significant
            if term['pvalue'] < 0.05:
                processed_data["significant_processes"].append(term['id'])
                processed_data["top_processes"].append({
                    "term_id": term['id'],
                    "p_value": term['pvalue'],
                    "enrichment_score": term['foldEnrichment']
                })
        
        return processed_data
        
    except requests.RequestException as e:
        print(f"Error fetching DAVID enrichment: {str(e)}")
        return {}

def save_biclique_enrichment_data(db: Session, biclique_id: int, timepoint_id: int, enrichment_data: Dict[str, Any]):
    """Save biclique GO enrichment data to database"""
    # Insert main enrichment data
    db.execute(
        insert(GoEnrichmentBiclique).values(
            biclique_id=biclique_id,
            timepoint_id=timepoint_id,
            go_terms=enrichment_data.get("go_terms", {}),
            p_value=min([term["p_value"] for term in enrichment_data.get("top_processes", [{"p_value": 1.0}])]),
            enrichment_score=max([term["enrichment_score"] for term in enrichment_data.get("top_processes", [{"enrichment_score": 0.0}])]),
            source="DAVID",
            biologicalProcessCount=len(enrichment_data.get("go_terms", {})),
            significantBiologicalProcesses=enrichment_data.get("significant_processes", []),
            topBiologicalProcess=enrichment_data.get("significant_processes", [""])[0],
            biologicalProcessAnnotationDetails=enrichment_data.get("process_details", {})
        )
    )
    
    # Insert top processes
    for process in enrichment_data.get("top_processes", []):
        db.execute(
            insert(TopGoProcessesBiclique).values(
                biclique_id=biclique_id,
                timepoint_id=timepoint_id,
                termId=process["term_id"],
                pValue=process["p_value"],
                enrichmentScore=process["enrichment_score"]
            )
        )
    
    db.commit()

def process_biclique_enrichment(db: Session, biclique_id: int, timepoint_id: int) -> Dict[str, Any]:
    """
    Process GO enrichment for a biclique using DAVID API:
    1. Get all genes in biclique
    2. Get their NCBI IDs
    3. Fetch enrichment from DAVID
    4. Save to database
    
    Args:
        db: Database session
        biclique_id: ID of the biclique
        timepoint_id: ID of the timepoint
    
    Returns:
        Dictionary containing enrichment results
    """
    # Check for existing enrichment data
    stored_data = get_stored_biclique_enrichment(db, biclique_id, timepoint_id)
    if stored_data:
        return stored_data
    
    # Get genes in biclique
    gene_ids = get_biclique_genes(db, biclique_id, timepoint_id)
    if not gene_ids:
        return {"error": "No genes found in biclique"}
    
    # Get NCBI IDs
    ncbi_id_mapping = get_ncbi_ids_for_genes(db, gene_ids)
    if not ncbi_id_mapping:
        return {"error": "No NCBI IDs found for genes"}
    
    # Get unique NCBI IDs
    ncbi_ids = list(set(ncbi_id_mapping.values()))
    
    # Fetch enrichment from DAVID
    enrichment_data = fetch_david_enrichment(ncbi_ids)
    if not enrichment_data:
        return {"error": "Failed to fetch enrichment data from DAVID"}
    
    # Save enrichment data
    try:
        save_biclique_enrichment_data(db, biclique_id, timepoint_id, enrichment_data)
    except Exception as e:
        return {"error": f"Failed to save enrichment data: {str(e)}"}
    
    return enrichment_data

from sqlalchemy.orm import Session 
from sqlalchemy import select, insert
from typing import List, Dict, Any
import requests
import json
from datetime import datetime
from ..schemas import (
    EdgeDetails, 
    GeneDetails, 
    GoEnrichmentDmr, 
    TopGoProcessesDmr,
    GoEnrichmentBiclique,
    TopGoProcessesBiclique,
    BicliqueMemberSchema
)

def get_adjacent_genes_for_dmr(db: Session, dmr_id: int, timepoint_id: int) -> List[int]:
    """Get all genes adjacent to a DMR"""
    query = select(EdgeDetails.gene_id).where(
        EdgeDetails.dmr_id == dmr_id,
        EdgeDetails.timepoint_id == timepoint_id
    )
    result = db.execute(query)
    return [row[0] for row in result]

def get_ncbi_ids_for_genes(db: Session, gene_ids: List[int]) -> Dict[int, str]:
    """Get NCBI IDs for a list of genes"""
    query = select(GeneDetails.gene_id, GeneDetails.NCBI_id).where(
        GeneDetails.gene_id.in_(gene_ids)
    )
    result = db.execute(query)
    return {row.gene_id: row.NCBI_id for row in result if row.NCBI_id}

def get_stored_enrichment(db: Session, dmr_id: int, timepoint_id: int) -> Dict[str, Any]:
    """Get stored GO enrichment data if it exists"""
    query = select(GoEnrichmentDmr).where(
        GoEnrichmentDmr.dmr_id == dmr_id,
        GoEnrichmentDmr.timepoint_id == timepoint_id
    )
    result = db.execute(query).first()
    if result:
        # Get top processes
        top_processes = db.execute(
            select(TopGoProcessesDmr).where(
                TopGoProcessesDmr.dmr_id == dmr_id,
                TopGoProcessesDmr.timepoint_id == timepoint_id
            )
        ).fetchall()
        
        return {
            "go_terms": result.go_terms,
            "p_value": float(result.p_value),
            "enrichment_score": float(result.enrichment_score),
            "source": result.source,
            "biological_process_count": result.biologicalProcessCount,
            "significant_processes": result.significantBiologicalProcesses,
            "top_process": result.topBiologicalProcess,
            "process_details": result.biologicalProcessAnnotationDetails,
            "top_processes": [
                {
                    "term_id": p.termId,
                    "p_value": float(p.pValue), 
                    "enrichment_score": float(p.enrichmentScore)
                }
                for p in top_processes
            ]
        }
    return None

def fetch_go_enrichment(ncbi_ids: List[str], organism: str = "human") -> Dict[str, Any]:
    """
    Fetch GO enrichment data for a list of NCBI IDs
    
    Args:
        ncbi_ids: List of NCBI gene IDs
        organism: Either "human" or "mouse"
    
    Returns:
        Dictionary containing enrichment results
    """
    # TODO: Replace with actual GO enrichment API endpoint
    api_url = "https://api.example.com/go-enrichment"
    
    try:
        response = requests.post(api_url, json={
            "genes": ncbi_ids,
            "organism": organism
        })
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching GO enrichment: {str(e)}")
        return {}

def save_enrichment_data(db: Session, dmr_id: int, timepoint_id: int, enrichment_data: Dict[str, Any]):
    """Save GO enrichment data to database"""
    # Insert main enrichment data
    db.execute(
        insert(GoEnrichmentDmr).values(
            dmr_id=dmr_id,
            timepoint_id=timepoint_id,
            go_terms=enrichment_data.get("go_terms", {}),
            p_value=enrichment_data.get("p_value", 0.0),
            enrichment_score=enrichment_data.get("enrichment_score", 0.0),
            source="GO API",
            biologicalProcessCount=enrichment_data.get("process_count", 0),
            significantBiologicalProcesses=enrichment_data.get("significant_processes", []),
            topBiologicalProcess=enrichment_data.get("top_process", ""),
            biologicalProcessAnnotationDetails=enrichment_data.get("process_details", {})
        )
    )
    
    # Insert top processes
    for process in enrichment_data.get("top_processes", []):
        db.execute(
            insert(TopGoProcessesDmr).values(
                dmr_id=dmr_id,
                timepoint_id=timepoint_id,
                termId=process["term_id"],
                pValue=process["p_value"],
                enrichmentScore=process["enrichment_score"]
            )
        )
    
    db.commit()

def process_dmr_enrichment(db: Session, dmr_id: int, timepoint_id: int) -> Dict[str, Any]:
    """
    Process GO enrichment for a DMR:
    1. Check if enrichment exists in database
    2. If not:
    a. Get adjacent genes
    b. Get their NCBI IDs
    c. Fetch GO enrichment data
    d. Save to database
    3. Return enrichment data
    
    Args:
        db: Database session
        dmr_id: ID of the DMR
        timepoint_id: ID of the timepoint
    
    Returns:
        Dictionary containing processed enrichment results
    """
    # Check for existing enrichment data
    stored_data = get_stored_enrichment(db, dmr_id, timepoint_id)
    if stored_data:
        return stored_data
        
    # Get adjacent genes
    gene_ids = get_adjacent_genes_for_dmr(db, dmr_id, timepoint_id)
    if not gene_ids:
        return {"error": "No adjacent genes found for DMR"}
    
    # Get NCBI IDs for the genes
    ncbi_id_mapping = get_ncbi_ids_for_genes(db, gene_ids)
    if not ncbi_id_mapping:
        return {"error": "No NCBI IDs found for adjacent genes"}
    
    # Get unique NCBI IDs
    ncbi_ids = list(set(ncbi_id_mapping.values()))
    
    # Fetch GO enrichment data
    enrichment_data = fetch_go_enrichment(ncbi_ids)
    if not enrichment_data:
        return {"error": "Failed to fetch GO enrichment data"}
    
    # Save enrichment data to database
    try:
        save_enrichment_data(db, dmr_id, timepoint_id, enrichment_data)
    except Exception as e:
        return {"error": f"Failed to save enrichment data: {str(e)}"}
    
    return enrichment_data

