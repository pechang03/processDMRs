-- Create Timepoints Table
CREATE TABLE timepoints (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT
);

-- Create Master Gene IDs Table
CREATE TABLE master_gene_ids (
    id INTEGER PRIMARY KEY,
    gene_symbol VARCHAR(255) NOT NULL UNIQUE
);

-- Create Genes Table
CREATE TABLE genes (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    master_gene_id INTEGER REFERENCES master_gene_ids(id)
);

-- Create DMRs Table
CREATE TABLE dmrs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    area_stat FLOAT,
    description TEXT
);

-- Create Bicliques Table
CREATE TABLE bicliques (
    id SERIAL PRIMARY KEY,
    timepoint_id INTEGER REFERENCES timepoints(id),
    component_id INTEGER,
    dmr_ids INTEGER[] NOT NULL,
    gene_ids INTEGER[] NOT NULL
);

-- Create Components Table
CREATE TABLE components (
    id SERIAL PRIMARY KEY,
    timepoint_id INTEGER REFERENCES timepoints(id),
    category VARCHAR(50),
    size INTEGER,
    dmr_count INTEGER,
    gene_count INTEGER,
    edge_count INTEGER,
    density FLOAT
);

-- Create Junction Table for Components and Bicliques
CREATE TABLE component_bicliques (
    component_id INTEGER REFERENCES components(id),
    biclique_id INTEGER REFERENCES bicliques(id),
    PRIMARY KEY (component_id, biclique_id)
);

-- Create Statistics Table
CREATE TABLE statistics (
    id SERIAL PRIMARY KEY,
    category VARCHAR(50),
    key VARCHAR(255),
    value TEXT
);

-- Create Metadata Table
CREATE TABLE metadata (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50),
    entity_id INTEGER,
    key VARCHAR(255),
    value TEXT
);

-- Create Relationships Table
CREATE TABLE relationships (
    id SERIAL PRIMARY KEY,
    source_entity_type VARCHAR(50),
    source_entity_id INTEGER,
    target_entity_type VARCHAR(50),
    target_entity_id INTEGER,
    relationship_type VARCHAR(50)
);

-- Indexing for Performance
CREATE INDEX idx_timepoints_name ON timepoints(name);
CREATE INDEX idx_genes_symbol ON genes(symbol);
CREATE INDEX idx_bicliques_timepoint ON bicliques(timepoint_id);
CREATE INDEX idx_bicliques_component ON bicliques(component_id);
CREATE INDEX idx_component_bicliques ON component_bicliques(component_id, biclique_id);
