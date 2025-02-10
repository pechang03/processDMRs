from typing import Set, Dict
from backend.app.utils.constants import START_GENE_ID

# Preloaded dictionary of DMR_ID_OFFSET values from the Timepoint table;
# keys are timepoint IDs and values are the offsets.
TIMEPOINT_OFFSETS = {
    1: 0,
    2: 10000,
    3: 20000,
    4: 30000,
    5: 40000,
    6: 50000,
    7: 60000,
    8: 70000,
}


# Cache for timepoint offsets
def convert_dmr_id(
    dmr_num: int,
    timepoint: int or str,
    is_original: bool = True,
    first_gene_id: int = 0,
) -> int:
    """Convert a DMR node ID to its final form based on graph type and timepoint.

    Args:
        dmr_num: Raw DMR number from graph
        timepoint: Timepoint ID (int) or name (str)
        is_original: Whether this is from original graph (needs +1) or split graph
        first_gene_id: Optional upper bound for DMR IDs

    Returns:
        Converted DMR ID with proper offset and adjustment
    """
    return create_dmr_id(dmr_num + 1, timepoint, first_gene_id)


def reverse_create_dmr_id(converted_id: int, timepoint: int, is_original: bool = True) -> int:
    """Convert a table DMR ID back to the raw (0-indexed) node ID.
    For original graphs, subtract the timepoint offset and 1; for split graphs, subtract the offset only.
    """
    if not isinstance(timepoint, int):
        raise TypeError("Expected timepoint to be an int")
    try:
        offset = TIMEPOINT_OFFSETS[timepoint]
    except KeyError:
        raise ValueError(f"Unknown timepoint_id {timepoint} in TIMEPOINT_OFFSETS")
    if is_original:
        return converted_id - offset - 1
    else:
        return converted_id - offset

def create_dmr_id(dmr_num: int, timepoint: int or str, first_gene_id: int = 0) -> int:
    """Create a unique DMR ID for a specific timepoint.

    If timepoint is an integer, it is assumed to be the dmr_id_offset.
    If it is a string, the offset is looked up from a fixed dictionary.
    """
    if not isinstance(timepoint, (int, str)):
        raise TypeError(
            f"create_dmr_id: Expected timepoint to be int or str, got {type(timepoint)}: {timepoint}"
        )
    if isinstance(timepoint, int):
        # Look up offset by timepoint_id in the preloaded dictionary
        try:
            offset = TIMEPOINT_OFFSETS[timepoint]
        except KeyError:
            raise ValueError(f"Unknown timepoint_id {timepoint} in TIMEPOINT_OFFSETS")
    else:
        # Define fixed offsets for each timepoint
        timepoint_offsets = {
            "DSStimeseries": 0,
            "P21-P28": 10000,
            "P21-P40": 20000,
            "P21-P60": 30000,
            "P21-P180": 40000,
            "TP28-TP180": 50000,
            "TP40-TP180": 60000,
            "TP60-TP180": 70000,
        }
        # Remove _TSS suffix if present for matching
        timepoint_clean = timepoint.replace("_TSS", "")
        # Get offset for this timepoint
        offset = timepoint_offsets.get(
            timepoint_clean, 80000
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

    # Convert all gene names to lowercase and remove any empty strings or invalid values
    cleaned_genes = set()
    seen_genes = set()  # Track genes we've already processed

    for gene in genes:
        if gene and isinstance(gene, str):
            gene_lower = gene.strip().lower()
            if (
                gene_lower not in seen_genes
                and gene_lower not in {".", "n/a", ""}
                and not gene_lower.startswith("unnamed:")
            ):
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
