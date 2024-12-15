from typing import Set, Dict
from utils.constants import START_GENE_ID

# Cache for timepoint offsets
_timepoint_offsets = {}

def _init_timepoint_offsets():
    """Initialize the timepoint offsets cache from database."""
    from database.models import Timepoint
    from database.connection import get_db_session, get_db_engine
    
    global _timepoint_offsets
    
    if not _timepoint_offsets:  # Only load if cache is empty
        engine = get_db_engine()
        session = get_db_session(engine)
        timepoints = session.query(Timepoint).all()
        _timepoint_offsets = {tp.name: tp.dmr_id_offset for tp in timepoints}
        session.close()

def create_dmr_id(dmr_num: int, timepoint: str, first_gene_id: int = 0) -> int:
    """Create a unique DMR ID for a specific timepoint."""
    global _timepoint_offsets
    
    # Initialize cache if needed
    if not _timepoint_offsets:
        _init_timepoint_offsets()
    
    # Get offset from cache
    offset = _timepoint_offsets.get(timepoint)
    if offset is None:
        print(f"Warning: Timepoint {timepoint} not found in cache")
        return dmr_num
        
    # Calculate DMR ID with offset
    dmr_id = offset + dmr_num

    # Ensure DMR ID is below first gene ID
    if first_gene_id > 0 and dmr_id >= first_gene_id:
        print(
            f"Warning: DMR ID {dmr_id} would exceed first gene ID {first_gene_id}, using original numbering"
        )
        dmr_id = dmr_num  # Fall back to original numbering

    return dmr_id

def clear_timepoint_cache():
    """Clear the timepoint offsets cache."""
    global _timepoint_offsets
    _timepoint_offsets = {}


def create_gene_mapping(genes: Set[str], max_dmr_id: int = None) -> Dict[str, int]:
    """Create a mapping of gene names to IDs starting at START_GENE_ID."""
    print(f"\nCreating gene ID mapping for {len(genes)} unique genes")

    # Convert all gene names to lowercase and remove any empty strings or invalid values
    cleaned_genes = set()
    seen_genes = set()  # Track genes we've already processed
    
    for gene in genes:
        if gene and isinstance(gene, str):
            gene_lower = gene.strip().lower()
            if (gene_lower not in seen_genes and 
                gene_lower not in {".", "n/a", ""} and
                not gene_lower.startswith("unnamed:")):
                cleaned_genes.add(gene_lower)
                seen_genes.add(gene_lower)

    print(f"After cleaning: {len(cleaned_genes)} unique genes")
    print("First 5 cleaned genes:", sorted(list(cleaned_genes))[:5])

    # Create mapping starting at START_GENE_ID
    gene_id_mapping = {
        gene: START_GENE_ID + idx for idx, gene in enumerate(sorted(cleaned_genes))
    }

    # Validate no overlap with DMR IDs if max_dmr_id provided
    if max_dmr_id is not None and max_dmr_id >= START_GENE_ID:
        print(
            f"WARNING: Maximum DMR ID ({max_dmr_id}) is >= START_GENE_ID ({START_GENE_ID})"
        )
        print("This may cause DMR and gene ID ranges to overlap!")

    return gene_id_mapping


def validate_gene_mapping(gene_id_mapping: Dict[str, int], max_dmr_id: int) -> bool:
    """Validate that gene IDs don't overlap with DMR IDs."""
    min_gene_id = min(gene_id_mapping.values())
    if min_gene_id <= max_dmr_id:
        print(
            f"WARNING: Gene IDs start at {min_gene_id} but max DMR ID is {max_dmr_id}"
        )
        return False
    return True
