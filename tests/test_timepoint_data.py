import unittest
from routes.timepoint_data import process_timepoint
from biclique_analysis.processor import process_bicliques
from biclique_analysis.components import process_components


class TestTimepointData(unittest.TestCase):
    def test_timepoint_data_structure(self):
        """Test that timepoint data contains all required fields with correct structure"""
        # Mock data would go here
        timepoint_data = {
            "bicliques": [
                ([0, 1, 2, 3, 4], [102923, 103417]),
                # ... more bicliques
            ],
            "stats": {
                "coverage": {
                    "dmrs": {"covered": 2092, "total": 2109, "percentage": 0.99},
                    "genes": {"covered": 3636, "total": 4536, "percentage": 0.80},
                    "edges": {
                        "single_coverage": 10517,
                        "multiple_coverage": 0,
                        "uncovered": 1586,
                        "total": 12103,
                        "single_percentage": 0.87,
                        "multiple_percentage": 0.0,
                        "uncovered_percentage": 0.13,
                    },
                },
                "components": {
                    "original": {
                        "connected": {
                            "total": 0,
                            "single_node": 0,
                            "small": 0,
                            "interesting": 0,
                        },
                        "biconnected": {
                            "total": 0,
                            "single_node": 0,
                            "small": 0,
                            "interesting": 0,
                        },
                        "triconnected": {
                            "total": 0,
                            "single_node": 0,
                            "small": 0,
                            "interesting": 0,
                        },
                    },
                    "biclique": {
                        "connected": {
                            "total": 0,
                            "single_node": 0,
                            "small": 0,
                            "interesting": 0,
                        }
                    },
                },
            },
        }

        # Required fields that should be present
        required_fields = {
            "interesting_components": {
                "required_subfields": [
                    "id",
                    "dmrs",
                    "genes",
                    "size",
                    "category",
                    "raw_bicliques",
                ]
            },
            "complex_components": {
                "required_subfields": [
                    "id",
                    "dmrs",
                    "genes",
                    "size",
                    "category",
                    "raw_bicliques",
                ]
            },
            "bicliques": {
                "required_subfields": [
                    "dmrs",
                    "genes",
                ]  # Each biclique should be a tuple of dmrs and
            },
            "stats": {"required_subfields": ["coverage", "components"]},
            "bicliques_summary": {"required_subfields": ["graph_info", "header_stats"]},
        }

        # Test presence and structure of fields
        for field, requirements in required_fields.items():
            self.assertIn(field, timepoint_data, f"Missing required field: {field}")
            if requirements.get("required_subfields"):
                for subfield in requirements["required_subfields"]:
                    self.assertIn(
                        subfield,
                        timepoint_data[field],
                        f"Missing required subfield {subfield} in {field}",
                    )

        # Test component structure
        for component in timepoint_data.get("interesting_components", []):
            self.assertIsInstance(component["id"], int)
            self.assertIsInstance(component["dmrs"], int)
            self.assertIsInstance(component["genes"], int)
            self.assertIsInstance(component["size"], int)
            self.assertIsInstance(component["category"], str)
            self.assertIsInstance(component["raw_bicliques"], list)
