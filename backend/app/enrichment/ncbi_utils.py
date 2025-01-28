"""
Utilities for interacting with NCBI's E-utilities API to fetch gene information.

Environment variables required:
NCBI_EMAIL: Your registered email with NCBI
NCBI_API_KEY: Your NCBI API key from https://www.ncbi.nlm.nih.gov/account/settings/
DEFAULT_ORGANISM: Optional, set to "human" or "mouse" (defaults to "mouse")

To set up:
1. Create a NCBI account if you don't have one
2. Get your API key from NCBI account settings
3. Copy .env.example to .env and fill in your details
4. Make sure python-dotenv is installed: pip install python-dotenv
"""
import os
import time
from typing import Dict, List, Optional, Union
from functools import lru_cache
from Bio import Entrez
import logging
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv('processDMRs.env')

# Configure logging
logger = logging.getLogger(__name__)

# Configure Entrez from environment variables
Entrez.email = os.getenv('NCBI_EMAIL')
if not Entrez.email:
    raise ValueError("NCBI_EMAIL environment variable not set")

Entrez.api_key = os.getenv('NCBI_API_KEY')
if not Entrez.api_key:
    raise ValueError("NCBI_API_KEY environment variable not set")

# Get default organism from environment, fallback to "mouse"
DEFAULT_ORGANISM = os.getenv('DEFAULT_ORGANISM', 'mouse')

# Constants
RATE_LIMIT = 0.34  # Maximum 3 requests per second
CACHE_SIZE = 1000

@dataclass
class GeneInfo:
    """Data class to store gene information."""
    ncbi_id: str
    symbol: str
    description: str
    organism: str
    synonyms: List[str]
    raw_data: Dict

class NCBIError(Exception):
    """Base exception for NCBI-related errors."""
    pass

def rate_limit():
    """Simple rate limiting function."""
    time.sleep(RATE_LIMIT)

@lru_cache(maxsize=CACHE_SIZE)
def fetch_gene_id(gene_symbol: str, organism: str = "mouse") -> Optional[str]:
    """
    Fetch NCBI Gene ID for a given gene symbol.
    
    Args:
        gene_symbol: The gene symbol to look up
        organism: Either 'mouse' or 'human'
    
    Returns:
        NCBI Gene ID if found, None otherwise
    
    Raises:
        NCBIError: If there's an error communicating with NCBI
    """
    try:
        organism_term = "Mus musculus" if organism == "mouse" else "Homo sapiens"
        rate_limit()
        
        search_term = f"{gene_symbol}[Gene Symbol] AND {organism_term}[Organism]"
        handle = Entrez.esearch(db="gene", term=search_term)
        record = Entrez.read(handle)
        handle.close()
        
        if record["Count"] == "0":
            logger.warning(f"No NCBI ID found for gene {gene_symbol}")
            return None
            
        return record["IdList"][0]
        
    except Exception as e:
        logger.error(f"Error fetching NCBI ID for {gene_symbol}: {str(e)}")
        raise NCBIError(f"NCBI API error: {str(e)}")

@lru_cache(maxsize=CACHE_SIZE)
def fetch_gene_details(gene_id: str) -> Optional[GeneInfo]:
    """
    Fetch detailed information for a gene using its NCBI Gene ID.
    
    Args:
        gene_id: NCBI Gene ID
    
    Returns:
        GeneInfo object containing gene details
    
    Raises:
        NCBIError: If there's an error communicating with NCBI
    """
    try:
        rate_limit()
        handle = Entrez.efetch(db="gene", id=gene_id, retmode="xml")
        records = Entrez.read(handle)
        handle.close()
        
        if not records or "Entrezgene" not in records[0]:
            return None
            
        gene_data = records[0]["Entrezgene"]
        
        return GeneInfo(
            ncbi_id=gene_id,
            symbol=gene_data.get("Gene-ref", {}).get("Gene-ref_locus", ""),
            description=gene_data.get("Gene-ref", {}).get("Gene-ref_desc", ""),
            organism=gene_data.get("Source", {}).get("BioSource", {}).get("BioSource_org", {}).get("Org-ref", {}).get("Org-ref_taxname", ""),
            synonyms=gene_data.get("Gene-ref", {}).get("Gene-ref_syn", []),
            raw_data=gene_data
        )
        
    except Exception as e:
        logger.error(f"Error fetching gene details for ID {gene_id}: {str(e)}")
        raise NCBIError(f"NCBI API error: {str(e)}")

def bulk_fetch_gene_ids(gene_symbols: List[str], organism: str = "mouse") -> Dict[str, str]:
    """
    Fetch NCBI Gene IDs for multiple gene symbols.
    
    Args:
        gene_symbols: List of gene symbols to look up
        organism: Either 'mouse' or 'human'
    
    Returns:
        Dictionary mapping gene symbols to their NCBI IDs
    """
    results = {}
    for symbol in gene_symbols:
        try:
            ncbi_id = fetch_gene_id(symbol, organism)
            if ncbi_id:
                results[symbol] = ncbi_id
        except NCBIError as e:
            logger.error(f"Error in bulk fetch for {symbol}: {str(e)}")
            continue
    return results

def bulk_fetch_gene_details(ncbi_ids: List[str]) -> Dict[str, GeneInfo]:
    """
    Fetch detailed information for multiple genes.
    
    Args:
        ncbi_ids: List of NCBI Gene IDs
    
    Returns:
        Dictionary mapping NCBI IDs to GeneInfo objects
    """
    results = {}
    for gene_id in ncbi_ids:
        try:
            gene_info = fetch_gene_details(gene_id)
            if gene_info:
                results[gene_id] = gene_info
        except NCBIError as e:
            logger.error(f"Error in bulk fetch for ID {gene_id}: {str(e)}")
            continue
    return results

