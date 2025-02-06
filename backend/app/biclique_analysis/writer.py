"""Functions for writing biclique analysis results to files."""

import json
import csv
from typing import Dict, List, Tuple, Set
from pathlib import Path
from backend.app.utils.json_utils import convert_for_json

def write_bicliques(
    bicliques: List[Tuple[Set[int], Set[int]]],
    output_path: str,
    metadata: Dict = None
) -> None:
    """
    Write bicliques to file with optional metadata.
    
    Args:
        bicliques: List of (dmr_nodes, gene_nodes) tuples
        output_path: Path to output file
        metadata: Optional metadata for each biclique
    """
    try:
        output_path = Path(output_path)
        
        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            # Write header
            f.write("# Bicliques\n")
            f.write(f"# Total: {len(bicliques)}\n\n")
            
            # Write each biclique
            for idx, (dmr_nodes, gene_nodes) in enumerate(bicliques):
                # Write biclique header with metadata if available
                if metadata and idx in metadata:
                    meta = metadata[idx]
                    f.write(f"# Biclique {idx}: {meta.get('category', 'unknown')}\n")
                    f.write(f"# Size: {len(dmr_nodes)} DMRs, {len(gene_nodes)} genes\n")
                else:
                    f.write(f"# Biclique {idx}\n")
                
                # Write nodes (DMRs first, then genes)
                f.write(" ".join(map(str, sorted(dmr_nodes))))
                f.write(" ")
                f.write(" ".join(map(str, sorted(gene_nodes))))
                f.write("\n\n")
                
        print(f"Successfully wrote {len(bicliques)} bicliques to {output_path}")
        
    except Exception as e:
        print(f"Error writing bicliques to {output_path}: {str(e)}")
        raise

def write_analysis_results(
    results: Dict,
    output_path: str,
    include_debug: bool = False
) -> None:
    """
    Write complete analysis results to JSON file.
    
    Args:
        results: Dictionary containing analysis results
        output_path: Path to output file
        include_debug: Whether to include debug information
    """
    try:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert data for JSON serialization
        json_data = convert_for_json(results)
        
        # Optionally remove debug information
        if not include_debug and 'debug' in json_data:
            del json_data['debug']
        
        with open(output_path, 'w') as f:
            json.dump(json_data, f, indent=2)
            
        print(f"Successfully wrote analysis results to {output_path}")
        
    except Exception as e:
        print(f"Error writing analysis results to {output_path}: {str(e)}")
        raise

def write_component_details(
    components: List[Dict],
    output_path: str,
    include_positions: bool = True
) -> None:
    """
    Write detailed component information to CSV file.
    
    Args:
        components: List of component dictionaries
        output_path: Path to output file
        include_positions: Whether to include node positions
    """
    try:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        fieldnames = [
            'component_id',
            'category',
            'dmr_count',
            'gene_count',
            'total_nodes',
            'edge_count',
            'density',
            'biclique_count'
        ]
        
        if include_positions:
            fieldnames.extend(['positions'])
        
        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for comp in components:
                row = {
                    'component_id': comp.get('id'),
                    'category': comp.get('category', 'unknown'),
                    'dmr_count': comp.get('dmrs', 0),
                    'gene_count': comp.get('genes', 0),
                    'total_nodes': comp.get('size', 0),
                    'edge_count': comp.get('total_edges', 0),
                    'density': comp.get('density', 0),
                    'biclique_count': len(comp.get('raw_bicliques', []))
                }
                
                if include_positions and 'positions' in comp:
                    row['positions'] = json.dumps(comp['positions'])
                    
                writer.writerow(row)
                
        print(f"Successfully wrote component details to {output_path}")
        
    except Exception as e:
        print(f"Error writing component details to {output_path}: {str(e)}")
        raise
