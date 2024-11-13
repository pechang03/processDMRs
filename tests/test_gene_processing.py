import unittest
import pandas as pd
from biclique_analysis.processor import process_enhancer_info

class TestGeneProcessing(unittest.TestCase):
    def test_gene_name_processing(self):
        # Test basic gene name processing
        enhancer_info = "Gene1/123; Gene2/456; Gene3/789"
        result = process_enhancer_info(enhancer_info)
        self.assertEqual(result, {"Gene1", "Gene2", "Gene3"})

    def test_duplicate_gene_handling(self):
        # Test handling of duplicate genes
        enhancer_info = "Gene1/123; Gene1/456; Gene1/789"
        result = process_enhancer_info(enhancer_info)
        self.assertEqual(result, {"Gene1"})

    def test_mixed_gene_formats(self):
        # Test handling of mixed formats (with and without suffixes)
        enhancer_info = "Gene1/123; Gene2; Gene3/789"
        result = process_enhancer_info(enhancer_info)
        self.assertEqual(result, {"Gene1", "Gene2", "Gene3"})

    def test_empty_input(self):
        # Test handling of empty input
        self.assertEqual(process_enhancer_info(""), set())
        self.assertEqual(process_enhancer_info(None), set())
        self.assertEqual(process_enhancer_info(pd.NA), set())

    def test_whitespace_handling(self):
        # Test handling of whitespace
        enhancer_info = "  Gene1/123  ;  Gene2/456  ;  Gene3/789  "
        result = process_enhancer_info(enhancer_info)
        self.assertEqual(result, {"Gene1", "Gene2", "Gene3"})

    def test_total_gene_count(self):
        # Test that total gene count matches expected after processing
        # Create a small test DataFrame
        data = {
            'Gene_Symbol_Nearby': ['GeneA/123', 'GeneB/456', 'GeneA/789'],
            'ENCODE_Enhancer_Interaction(BingRen_Lab)': [
                'GeneC/123; GeneD/456',
                'GeneB/789; GeneE/012',
                'GeneA/345; GeneF/678'
            ]
        }
        df = pd.DataFrame(data)
        
        # Process all genes
        all_genes = set()
        
        # Add genes from Gene_Symbol_Nearby
        all_genes.update([g.split('/')[0].strip() for g in df['Gene_Symbol_Nearby'].dropna()])
        
        # Add genes from enhancer interactions
        for enhancer_info in df['ENCODE_Enhancer_Interaction(BingRen_Lab)'].dropna():
            all_genes.update(process_enhancer_info(enhancer_info))
        
        # Check total unique genes
        self.assertEqual(len(all_genes), 6)  # Should be GeneA through GeneF
        expected_genes = {'GeneA', 'GeneB', 'GeneC', 'GeneD', 'GeneE', 'GeneF'}
        self.assertEqual(all_genes, expected_genes)

if __name__ == '__main__':
    unittest.main()
