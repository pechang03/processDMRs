import pandas as pd

def process_enhancer_info(interaction_info):
    """Process enhancer/promoter interaction information.

    Args:
        interaction_info: String containing semicolon-separated gene/enrichment pairs

    Returns:
        Set of valid gene names (excluding '.' entries, only gene part before /)
    """
    if pd.isna(interaction_info) or not interaction_info:
        return set()

    genes = set()
    for entry in str(interaction_info).split(";"):
        entry = entry.strip()
        # Skip '.' entries
        if entry == ".":
            continue

        # Split on / and take only the gene part
        if "/" in entry:
            gene = entry.split("/")[0].strip()
        else:
            gene = entry.strip()

        if gene:  # Only add non-empty genes
            genes.add(gene)

    return genes
