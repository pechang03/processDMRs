"""Tests for dominating set database functionality."""

import unittest
import networkx as nx
import pandas as pd
from sqlalchemy.orm import Session
from backend.app.database.connection import get_db_engine
from backend.app.database.models import DominatingSet, Timepoint
from backend.app.database.operations import store_dominating_set, get_dominating_set

class TestDominatingSetStorage(unittest.TestCase):
    def setUp(self):
        """Set up test database and sample data."""
        self.engine = get_db_engine()
        
        # Create all tables before starting tests
        from backend.app.database.models import Base
        Base.metadata.create_all(self.engine)
        
        self.session = Session(self.engine)
        
        # Create test timepoint
        self.timepoint = Timepoint(name="test_timepoint", sheet_name="test_timepoint_TSS", description="Test timepoint")
        self.session.add(self.timepoint)
        self.session.commit()
        
        # Sample dominating set data
        self.dominating_set = {1, 2, 3}
        self.area_stats = {1: 0.5, 2: 0.7, 3: 0.3}
        self.utility_scores = {1: 0.8, 2: 0.6, 3: 0.9}
        self.dominated_counts = {1: 5, 2: 3, 3: 4}

    def tearDown(self):
        """Clean up test database."""
        self.session.query(DominatingSet).delete()
        self.session.query(Timepoint).delete()
        self.session.commit()
        
        # Drop all tables after tests
        from backend.app.database.models import Base
        Base.metadata.drop_all(self.engine)
        
        self.session.close()

    def test_store_dominating_set(self):
        """Test storing dominating set in database."""
        store_dominating_set(
            self.session,
            self.timepoint.id,
            self.dominating_set,
            self.area_stats,
            self.utility_scores,
            self.dominated_counts
        )
        
        # Verify storage
        stored_entries = self.session.query(DominatingSet).filter_by(
            timepoint_id=self.timepoint.id
        ).all()
        
        self.assertEqual(len(stored_entries), len(self.dominating_set))
        stored_dmrs = {entry.dmr_id for entry in stored_entries}
        self.assertEqual(stored_dmrs, self.dominating_set)
        
        # Check metadata
        for entry in stored_entries:
            self.assertEqual(entry.area_stat, self.area_stats[entry.dmr_id])
            self.assertEqual(entry.utility_score, self.utility_scores[entry.dmr_id])
            self.assertEqual(entry.dominated_gene_count, self.dominated_counts[entry.dmr_id])

    def test_get_dominating_set(self):
        """Test retrieving dominating set from database."""
        # First store the data
        store_dominating_set(
            self.session,
            self.timepoint.id,
            self.dominating_set,
            self.area_stats,
            self.utility_scores,
            self.dominated_counts
        )
        
        # Retrieve and verify
        retrieved_set, metadata = get_dominating_set(self.session, self.timepoint.id)
        
        self.assertEqual(retrieved_set, self.dominating_set)
        self.assertEqual(metadata['area_stats'], self.area_stats)
        self.assertEqual(metadata['utility_scores'], self.utility_scores)
        self.assertEqual(metadata['dominated_counts'], self.dominated_counts)
        self.assertIsNotNone(metadata['calculation_timestamp'])

    def test_dominating_set_update(self):
        """Test updating existing dominating set."""
        # Store initial data
        store_dominating_set(
            self.session,
            self.timepoint.id,
            self.dominating_set,
            self.area_stats,
            self.utility_scores,
            self.dominated_counts
        )
        
        # Update with new data
        new_dominating_set = {2, 3, 4}
        new_area_stats = {2: 0.8, 3: 0.4, 4: 0.6}
        new_utility_scores = {2: 0.7, 3: 0.8, 4: 0.5}
        new_dominated_counts = {2: 4, 3: 5, 4: 3}
        
        store_dominating_set(
            self.session,
            self.timepoint.id,
            new_dominating_set,
            new_area_stats,
            new_utility_scores,
            new_dominated_counts
        )
        
        # Verify update
        retrieved_set, metadata = get_dominating_set(self.session, self.timepoint.id)
        self.assertEqual(retrieved_set, new_dominating_set)
        self.assertEqual(metadata['area_stats'], new_area_stats)
