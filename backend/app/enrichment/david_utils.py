"""
DAVID (Database for Annotation, Visualization and Integrated Discovery) API utilities.
Handles gene list submission, enrichment analysis retrieval, and result processing.
"""

import time
from typing import List, Dict, Optional, Any
import requests
from pathlib import Path
import json
from functools import lru_cache
import logging
from dotenv import load_dotenv
import os

# Load configuration
load_dotenv(Path("./processDMRs.env"))

DAVID_EMAIL = os.getenv("DAVID_EMAIL")
DAVID_API_KEY = os.getenv("DAVID_API_KEY")

# Constants
DAVID_BASE_URL = "https://david.ncifcrf.gov/api.jsp"
CACHE_DIR = Path("./cache/david")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)

class DAVIDError(Exception):
    """Custom exception for DAVID API related errors."""
    pass

def get_cache_key(gene_ids: List[str], species: str) -> str:
    """Generate a unique cache key for a gene list."""
    genes_str = "_".join(sorted(gene_ids))
    return f"{species}_{hash(genes_str)}"

@lru_cache(maxsize=128)
def load_cached_results(cache_key: str) -> Optional[Dict]:
    """Load cached enrichment results if they exist."""
    cache_file = CACHE_DIR / f"{cache_key}.json"
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Failed to load cache file: {cache_file}")
            return None
    return None

def save_to_cache(cache_key: str, data: Dict) -> None:
    """Save enrichment results to cache."""
    cache_file = CACHE_DIR / f"{cache_key}.json"
    try:
        with open(cache_file, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        logger.error(f"Failed to save to cache: {e}")

def submit_gene_list(gene_ids: List[str], species: str = "mouse") -> str:
    """
    Submit a list of gene IDs to DAVID for analysis.

    Args:
        gene_ids: List of NCBI gene IDs
        species: Species identifier ('mouse' or 'human')

    Returns:
        str: Job ID for the submitted analysis

    Raises:
        DAVIDError: If submission fails
    """
    if not DAVID_EMAIL or not DAVID_API_KEY:
        raise DAVIDError("DAVID credentials not configured")

    try:
        payload = {
            "api_key": DAVID_API_KEY,
            "email": DAVID_EMAIL,
            "genes": ",".join(gene_ids),
            "species": "mouse" if species.lower() == "mouse" else "human",
            "tool": "chartReport",
            "annot": "GOTERM_BP_DIRECT,GOTERM_CC_DIRECT,GOTERM_MF_DIRECT"
        }
        
        response = requests.post(DAVID_BASE_URL, data=payload)
        response.raise_for_status()
        
        job_id = response.text.strip()
        if not job_id:
            raise DAVIDError("No job ID returned from DAVID")
        
        return job_id
        
    except requests.RequestException as e:
        logger.error(f"DAVID API submission failed: {e}")
        raise DAVIDError(f"Failed to submit gene list to DAVID: {e}")

def get_enrichment_results(job_id: str, max_retries: int = 3) -> Dict:
    """
    Retrieve enrichment analysis results from DAVID.

    Args:
        job_id: Analysis job ID from submit_gene_list
        max_retries: Maximum number of retry attempts

    Returns:
        Dict containing enrichment results

    Raises:
        DAVIDError: If retrieval fails
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(
                DAVID_BASE_URL,
                params={
                    "api_key": DAVID_API_KEY,
                    "job_id": job_id,
                    "format": "json"
                }
            )
            response.raise_for_status()
            
            results = response.json()
            if results.get("status") == "RUNNING":
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
                
            return results
            
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to retrieve DAVID results: {e}")
                raise DAVIDError(f"Failed to get enrichment results: {e}")
            time.sleep(2 ** attempt)

    raise DAVIDError("Maximum retries exceeded while waiting for results")

def process_enrichment_results(results: Dict) -> Dict[str, List[Dict]]:
    """
    Process and format DAVID enrichment results.

    Args:
        results: Raw results from DAVID API

    Returns:
        Dict with processed results grouped by GO category
    """
    processed = {
        "biological_process": [],
        "cellular_component": [],
        "molecular_function": []
    }
    
    for entry in results.get("chartReport", []):
        category = entry.get("category", "").lower()
        if "bp_direct" in category:
            target = "biological_process"
        elif "cc_direct" in category:
            target = "cellular_component"
        elif "mf_direct" in category:
            target = "molecular_function"
        else:
            continue
            
        processed[target].append({
            "term": entry.get("term"),
            "count": entry.get("count"),
            "p_value": entry.get("pvalue"),
            "fdr": entry.get("fdr"),
            "genes": entry.get("genes", "").split(","),
            "fold_enrichment": entry.get("fold_enrichment")
        })
        
    return processed

def run_enrichment_analysis(
    gene_ids: List[str],
    species: str = "mouse",
    use_cache: bool = True
) -> Dict[str, List[Dict]]:
    """
    Run GO enrichment analysis for a list of genes using DAVID.

    Args:
        gene_ids: List of NCBI gene IDs
        species: Species identifier ('mouse' or 'human')
        use_cache: Whether to use cached results if available

    Returns:
        Dict containing processed enrichment results

    Raises:
        DAVIDError: If analysis fails
    """
    if not gene_ids:
        raise DAVIDError("Empty gene list provided")

    cache_key = get_cache_key(gene_ids, species)
    
    if use_cache:
        cached_results = load_cached_results(cache_key)
        if cached_results:
            logger.info(f"Using cached results for {cache_key}")
            return cached_results

    try:
        job_id = submit_gene_list(gene_ids, species)
        raw_results = get_enrichment_results(job_id)
        processed_results = process_enrichment_results(raw_results)
        
        if use_cache:
            save_to_cache(cache_key, processed_results)
            
        return processed_results
        
    except Exception as e:
        logger.error(f"Enrichment analysis failed: {e}")
        raise DAVIDError(f"Enrichment analysis failed: {e}")

