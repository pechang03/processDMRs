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
import re
from typing import Dict, List, Optional, Union
from urllib.error import HTTPError
from ..database.models import Gene, GeneDetails
from sqlalchemy.orm import Session
from functools import lru_cache
from Bio import Entrez
import logging
from dataclasses import dataclass
from flask import current_app
from werkzeug.exceptions import HTTPException
from sqlalchemy import text
def fetch_gene_id_from_ensembl(session, gene_id: int) -> Optional[str]:
    """
    Given a gene's internal ID, query the ensembl_genes table and 
    return an identifier: prefer external_gene_id if available,
    otherwise extract the MGI id from the description.
    """
    query = text("SELECT external_gene_id, description FROM ensembl_genes WHERE gene_id = :gene_id")
    result = session.execute(query, {"gene_id": gene_id}).fetchone()
    if result:
        ext_id = result["external_gene_id"]
        if ext_id:
            return ext_id
        desc = result["description"] or ""
        match = re.search(r"Acc:MGI:(\d+)", desc)
        if match:
            return match.group(1)
    return None

# Configure logging
logger = logging.getLogger(__name__)

def configure_entrez():
    """
    Configure Entrez with credentials from Flask config or environment variables.
    Will try Flask config first if in a Flask context, then fall back to environment variables.
    Must be called before any NCBI operations.
    
    Raises:
        ValueError: If required NCBI credentials are missing from both Flask config and environment
    """
    # Try to get credentials from Flask first, fall back to env vars
    try:
        # Check if we're in a Flask context
        ctx = current_app.config
        Entrez.email = ctx.get('NCBI_EMAIL')
        Entrez.api_key = ctx.get('NCBI_API_KEY')
        
        # Try to get proxy settings from Flask config first
        http_proxy = ctx.get('HTTP_PROXY')
        https_proxy = ctx.get('HTTPS_PROXY')
        no_proxy = ctx.get('NO_PROXY')
        
        logger.debug(f"Proxy settings from Flask config: HTTP_PROXY={http_proxy}, HTTPS_PROXY={https_proxy}, NO_PROXY={no_proxy}")
    except RuntimeError:
        # Not in Flask context, that's ok
        logger.debug("Not in Flask context, using environment variables")
        http_proxy = None
        https_proxy = None
        no_proxy = None
    
    # Fall back to environment variables for proxy settings if not set from Flask
    http_proxy = http_proxy or os.getenv('HTTP_PROXY') or os.getenv('http_proxy')
    https_proxy = https_proxy or os.getenv('HTTPS_PROXY') or os.getenv('https_proxy')
    no_proxy = no_proxy or os.getenv('NO_PROXY') or os.getenv('no_proxy')
    
    logger.debug(f"Final proxy settings: HTTP_PROXY={http_proxy}, HTTPS_PROXY={https_proxy}, NO_PROXY={no_proxy}")
    
    # Configure proxies both in environment and directly in Entrez
    if http_proxy:
        os.environ['http_proxy'] = http_proxy
        logger.info(f"Setting HTTP proxy to {http_proxy}")
        Entrez.tool.set_http_proxy(http_proxy)
    
    if https_proxy:
        os.environ['https_proxy'] = https_proxy
        logger.info(f"Setting HTTPS proxy to {https_proxy}")
        # Also set HTTPS proxy for Entrez if different from HTTP
        if https_proxy != http_proxy:
            Entrez.tool.set_http_proxy(https_proxy)
    
    if no_proxy:
        os.environ['no_proxy'] = no_proxy
        logger.info(f"Setting NO_PROXY to {no_proxy}")
    
    # Fall back to environment variables if not set from Flask
    if not Entrez.email:
        Entrez.email = os.getenv('NCBI_EMAIL')
    if not Entrez.api_key:
        Entrez.api_key = os.getenv('NCBI_API_KEY')
    
    # Final check that we have the required credentials
    if not Entrez.email:
        msg = "NCBI_EMAIL not found in Flask config or environment variables"
        logger.error(msg)
        raise ValueError(msg)
        
    if not Entrez.api_key:
        msg = "NCBI_API_KEY not found in Flask config or environment variables"
        logger.error(msg)
        raise ValueError(msg)

# Get default organism from config or fallback to "mouse"
DEFAULT_ORGANISM = "mouse"
def get_default_organism():
    """Get default organism from Flask config or fallback to mouse."""
    try:
        return current_app.config.get('DEFAULT_ORGANISM', 'mouse')
    except RuntimeError:
        return 'mouse'  # Fallback when outside application context

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
def fetch_gene_id(gene_symbol: str, organism: str = "mouse", session: Optional[Session] = None, gene_id: Optional[int] = None) -> Optional[str]:
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
        if session and gene_id:
            ncbi = fetch_gene_id_from_ensembl(session, gene_id)
            if ncbi:
                return ncbi

        configure_entrez()
        organism_term = "Mus musculus" if organism == "mouse" else "Homo sapiens"
        rate_limit()

        search_term = f"{gene_symbol}[Gene Symbol] AND {organism_term}[Organism]"
        logger.debug(f"Searching NCBI Gene with term: {search_term}")
        
        try:
            handle = Entrez.esearch(db="gene", term=search_term)
            record = Entrez.read(handle)
            handle.close()
        except HTTPError as e:
            url = e.url if hasattr(e, 'url') else 'URL not available'
            logger.error(f"HTTP Error when fetching gene ID for {gene_symbol}: {str(e)}. URL: {url}")
            logger.error(f"Full error details: {e.read().decode() if hasattr(e, 'read') else 'No additional details'}")
            raise NCBIError(f"NCBI API HTTP error for gene {gene_symbol}: {str(e)}")

        if record["Count"] == "0":
            logger.warning(f"No NCBI ID found for gene {gene_symbol}")
            return None

        return record["IdList"][0]

    except Exception as e:
        logger.error(f"Error fetching NCBI ID for {gene_symbol}: {str(e)}")
        raise NCBIError(f"NCBI API error for gene {gene_symbol}: {str(e)}")


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
        configure_entrez()
        rate_limit()
        
        logger.debug(f"Fetching gene details for NCBI ID: {gene_id}")
        try:
            handle = Entrez.efetch(db="gene", id=gene_id, retmode="xml")
            records = Entrez.read(handle)
            handle.close()
        except HTTPError as e:
            url = e.url if hasattr(e, 'url') else 'URL not available'
            logger.error(f"HTTP Error when fetching gene details for ID {gene_id}: {str(e)}. URL: {url}")
            logger.error(f"Full error details: {e.read().decode() if hasattr(e, 'read') else 'No additional details'}")
            raise NCBIError(f"NCBI API HTTP error for gene ID {gene_id}: {str(e)}")

        if not records or "Entrezgene" not in records[0]:
            return None

        gene_data = records[0]["Entrezgene"]

        return GeneInfo(
            ncbi_id=gene_id,
            symbol=gene_data.get("Gene-ref", {}).get("Gene-ref_locus", ""),
            description=gene_data.get("Gene-ref", {}).get("Gene-ref_desc", ""),
            organism=gene_data.get("Source", {})
            .get("BioSource", {})
            .get("BioSource_org", {})
            .get("Org-ref", {})
            .get("Org-ref_taxname", ""),
            synonyms=gene_data.get("Gene-ref", {}).get("Gene-ref_syn", []),
            raw_data=gene_data,
        )

    except Exception as e:
        logger.error(f"Error fetching gene details for ID {gene_id}: {str(e)}")
        raise NCBIError(f"NCBI API error: {str(e)}")


def bulk_fetch_gene_ids(
    gene_symbols: List[str], organism: str = "mouse"
) -> Dict[str, str]:
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


def fetch_ncbi_gene_ids(db: Session, gene_ids: List[int]) -> Dict[int, str]:
    """
    Fetch NCBI Gene IDs for a list of database gene IDs.
    First checks GeneDetails table for existing NCBI IDs,
    then uses bulk_fetch for any missing IDs.

    Args:
        db: SQLAlchemy database session
        gene_ids: List of gene IDs from the database

    Returns:
        Dictionary mapping gene_id (int) to NCBI_id (str)
    """
    gene_id_to_ncbi = {}

    # First check for existing NCBI IDs in GeneDetails table
    existing_details = (
        db.query(GeneDetails.gene_id, GeneDetails.NCBI_id)
        .filter(GeneDetails.gene_id.in_(gene_ids))
        .all()
    )

    # Add existing NCBI IDs to result dict
    for gene_id, ncbi_id in existing_details:
        if ncbi_id:  # Only add if NCBI ID exists
            gene_id_to_ncbi[gene_id] = ncbi_id

    # Find genes that don't have NCBI IDs yet
    missing_gene_ids = [gid for gid in gene_ids if gid not in gene_id_to_ncbi]

    if missing_gene_ids:
        # Fetch symbols for genes without NCBI IDs
        genes = (
            db.query(Gene.id, Gene.symbol).filter(Gene.id.in_(missing_gene_ids)).all()
        )

        # Map gene IDs to symbols for lookup
        id_to_symbol = {g.id: g.symbol for g in genes}
        symbols = [g.symbol for g in genes]

        # Fetch missing NCBI IDs using bulk fetch
        symbol_to_ncbi = bulk_fetch_gene_ids(symbols, organism=DEFAULT_ORGANISM)

        # Add newly fetched NCBI IDs to result dict
        for gene_id, symbol in id_to_symbol.items():
            if symbol in symbol_to_ncbi:
                gene_id_to_ncbi[gene_id] = symbol_to_ncbi[symbol]

    return gene_id_to_ncbi
