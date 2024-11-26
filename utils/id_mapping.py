from typing import Set, Dict
from utils.constants import START_GENE_ID


def create_dmr_id(dmr_num: int, timepoint: str, first_gene_id: int = 0) -> int:
    """Create a unique DMR ID for a specific timepoint."""
    # Use smaller offsets (e.g., 1000) for each timepoint to stay below START_GENE_ID
    timepoint_offsets = {
        "P21-P28_TSS": 10000,
        "P21-P40_TSS": 20000,
        "P21-P60_TSS": 30000,
        "P21-P180_TSS": 40000,
        "TP28-TP180_TSS": 50000,
        "TP40-TP180_TSS": 60000,
        "TP60-TP180_TSS": 70000,
        "DSS1": 0,  # Base timepoint uses original numbers
    }

    # Get offset for this timepoint
    offset = timepoint_offsets.get(
        timepoint, 8000
    )  # Default offset for unknown timepoints

    # Calculate DMR ID with offset
    dmr_id = offset + dmr_num

    # Ensure DMR ID is below first gene ID
    if first_gene_id > 0 and dmr_id >= first_gene_id:
        print(
            f"Warning: DMR ID {dmr_id} would exceed first gene ID {first_gene_id}, using original numbering"
        )
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
