#!/usr/bin/env python
"""
Migration script to copy data from the secondary database's `genes` table into
the primary database's ensembl_genes table. The migration uses Pydantic to validate
each record and merges based on matching the Genes.symbol field with the secondary table's Name.
"""

import os
from sqlalchemy import create_engine, text, func, inspect
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional

# Import models; note we need both EnsemblGene and Gene (for matching)
from backend.app.database.models import Base, EnsemblGene, Gene

# Load environment variables from project root
from backend.app.config import get_project_root
env_path = os.path.join(get_project_root(), "processDMR.env")
print(f"Loading environment from: {env_path}")

if not os.path.exists(env_path):
    raise FileNotFoundError(f"Environment file not found at: {env_path}")

load_dotenv(env_path)

# Get and verify database URLs
PRIMARY_DB_URL = os.environ.get("DATABASE_URL")
SECONDARY_DB_URL = os.environ.get("DATABASE_SECONDARY_URL")

print(f"Primary DB URL: {PRIMARY_DB_URL}")
print(f"Secondary DB URL: {SECONDARY_DB_URL}")

if not PRIMARY_DB_URL:
    raise ValueError("DATABASE_URL environment variable is not set")
if not SECONDARY_DB_URL:
    raise ValueError("DATABASE_SECONDARY_URL environment variable is not set")

# Create engines for both databases.
primary_engine = create_engine(PRIMARY_DB_URL)
secondary_engine = create_engine(SECONDARY_DB_URL)

# Check if ensembl_genes table exists and create if needed
inspector = inspect(primary_engine)
if not inspector.has_table("ensembl_genes"):
    Base.metadata.create_all(primary_engine, tables=[EnsemblGene.__table__])
    print("Created missing ensembl_genes table.")

PrimarySession = sessionmaker(bind=primary_engine)
primary_session = PrimarySession()


# Define a Pydantic model for the secondary genes table.
class SecondaryGene(BaseModel):
    chr: str
    source: str
    type: str
    start: int
    stop: int
    score: Optional[int] = None
    strand: str
    phase: Optional[int] = None
    ID: str
    Name: str
    Parent: Optional[int] = None
    Dbxref: Optional[int] = None
    gene_id: str
    mgi_type: Optional[str] = None
    description: Optional[str] = None


# Open a connection to the secondary database.
with secondary_engine.connect() as secondary_conn:
    query = text("""
        SELECT 
          "chr",
          source,
          type,
          start,
          stop,
          score,
          strand,
          phase,
          "ID",
          "Name",
          Parent,
          Dbxref,
          gene_id,
          mgi_type,
          description
        FROM genes
    """)
    result = secondary_conn.execute(query)

    migrated = 0
    for row in result:
        # Build a dict from row; keys match our Pydantic schema
        data = dict(row._mapping)
        try:
            # Validate and parse the row using Pydantic.
            sec_gene = SecondaryGene(**data)
        except Exception as e:
            print(f"Skipping row due to validation error: {e}")
            continue

        # Find the matching gene record in the primary database.
        # The Genes.symbol field should match sec_gene.Name (case-insensitive).
        primary_gene = (
            primary_session.query(Gene)
            .filter(func.lower(Gene.symbol) == sec_gene.Name.lower())
            .first()
        )
        if not primary_gene:
            print(
                f"Warning: No gene found in primary DB matching '{sec_gene.Name}'. Skipping record."
            )
            continue

        # Create an EnsemblGene record; use the found primary_gene.id as the linking gene_id.
        record = EnsemblGene(
            gene_id=primary_gene.id,  # linking field from Genes
            chr=sec_gene.chr,
            source=sec_gene.source,
            type=sec_gene.type,
            start=sec_gene.start,
            stop=sec_gene.stop,
            score=sec_gene.score,
            strand=sec_gene.strand,
            phase=sec_gene.phase,
            ensembl_id=sec_gene.ID,  # external ID
            name_external=sec_gene.Name,  # comes from secondary "Name"
            parent=sec_gene.Parent,
            dbxref=sec_gene.Dbxref,
            external_gene_id=sec_gene.gene_id,
            mgi_type=sec_gene.mgi_type,
            description=sec_gene.description,
        )
        primary_session.merge(record)
        migrated += 1

primary_session.commit()
print(f"Migrated {migrated} gene records from secondary database.")
primary_session.close()
