from typing import Set, Dict
from utils.constants import START_GENE_ID

def create_dmr_id(dmr_num: int, timepoint: str, first_gene_id: int = 0) -> int:
    """Create a unique DMR ID for a specific timepoint."""
    # Use a large offset (e.g., 1000000) for each timepoint to ensure no overlap
    timepoint_offsets = {
        "P21-P28": 1000000,
        "P21-P40": 2000000,
        "P21-P60": 3000000,
        "P21-P180": 4000000,
        "TP28-TP180": 5000000,
        "TP40-TP180": 6000000,
        "TP60-TP180": 7000000,
        "DSS1": 0  # Base timepoint uses original numbers
    }
    
    # Get offset for this timepoint
    offset = timepoint_offsets.get(timepoint, 8000000)  # Default offset for unknown timepoints
    
    # Calculate DMR ID with offset
    dmr_id = offset + dmr_num
    
    # Ensure DMR ID is below first gene ID if provided
    if first_gene_id > 0:
        if dmr_id >= first_gene_id:
            print(f"Warning: DMR ID {dmr_id} would exceed first gene ID {first_gene_id}")
            # Use alternative ID space below first_gene_id
            dmr_id = dmr_num  # Fall back to original numbering
            
    return dmr_id

def create_gene_mapping(genes: Set[str], max_dmr_id: int = None) -> Dict[str, int]:
    """Create a mapping of gene names to IDs starting at START_GENE_ID."""
    print(f"\nCreating gene ID mapping for {len(genes)} unique genes")

    # Convert all gene names to lowercase and remove any empty strings
    cleaned_genes = {
        gene.strip().lower() for gene in genes if gene and isinstance(gene, str)
    }
    cleaned_genes.discard("")
    
    print(f"After cleaning: {len(cleaned_genes)} unique genes")

    # Create mapping starting at START_GENE_ID
    gene_id_mapping = {
        gene: START_GENE_ID + idx for idx, gene in enumerate(sorted(cleaned_genes))
    }

    # Validate no overlap with DMR IDs if max_dmr_id provided
    if max_dmr_id is not None and max_dmr_id >= START_GENE_ID:
        print(f"WARNING: Maximum DMR ID ({max_dmr_id}) is >= START_GENE_ID ({START_GENE_ID})")
        print("This may cause DMR and gene ID ranges to overlap!")

    return gene_id_mapping

def validate_gene_mapping(gene_id_mapping: Dict[str, int], max_dmr_id: int) -> bool:
    """Validate that gene IDs don't overlap with DMR IDs."""
    min_gene_id = min(gene_id_mapping.values())
    if min_gene_id <= max_dmr_id:
        print(f"WARNING: Gene IDs start at {min_gene_id} but max DMR ID is {max_dmr_id}")
        return False
    return True
