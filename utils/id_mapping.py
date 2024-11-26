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
    offset = timepoint_offsets.get(timepoint, 8000000)  # Default offset for unknown timepoints
    
    # Ensure DMR IDs are below the first gene ID
    return min(first_gene_id - 1, offset + dmr_num)
