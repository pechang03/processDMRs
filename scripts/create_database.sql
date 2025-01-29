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

-- Create DMR IDs Table with timepoint relationship and offset handling
CREATE TABLE dmrs (
    id INTEGER PRIMARY KEY,
    timepoint_id INTEGER REFERENCES timepoints(id),
    dmr_number INTEGER NOT NULL,  -- Original DMR number before offset
    area_stat FLOAT,
    description TEXT,
    -- Common Excel file columns
    dmr_name VARCHAR(255),
    gene_description TEXT,
    chromosome VARCHAR(50),
    start_position INTEGER,
    end_position INTEGER,
    strand VARCHAR(1),
    p_value FLOAT,
    q_value FLOAT,
    mean_methylation FLOAT,
    -- Add constraint to ensure unique DMR numbers within a timepoint
    UNIQUE(timepoint_id, dmr_number)
);

-- Create index for efficient DMR lookups
CREATE INDEX idx_dmrs_timepoint ON dmrs(timepoint_id);
CREATE INDEX idx_dmrs_number ON dmrs(dmr_number);

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

-- Create Edge Details Table
CREATE TABLE edge_details (
    dmr_id INTEGER,
    gene_id INTEGER,
    timepoint_id INTEGER,
    edge_type VARCHAR(50),
    edit_type VARCHAR(50),
    distance_from_tss INTEGER,
    description TEXT,
    PRIMARY KEY (dmr_id, gene_id, timepoint_id),
    FOREIGN KEY (dmr_id) REFERENCES dmrs(id),
    FOREIGN KEY (gene_id) REFERENCES genes(id),
    FOREIGN KEY (timepoint_id) REFERENCES timepoints(id)
);

-- Create index for efficient lookups
CREATE INDEX idx_edge_details_lookup ON edge_details(dmr_id, gene_id, timepoint_id);

-- Create Gene Details Table
CREATE TABLE gene_details (
    gene_id INTEGER PRIMARY KEY,
    gene_name_long VARCHAR(50),
    genome VARCHAR(50),
    NCBI_id VARCHAR(50),
    annotations JSON,
    FOREIGN KEY (gene_id) REFERENCES genes(id)
);

-- Create index for NCBI_id lookups
CREATE INDEX idx_gene_details_ncbi ON gene_details(NCBI_id);

-- Create GO Enrichment DMR Table
CREATE TABLE go_enrichment_dmr (
    dmr_id INTEGER PRIMARY KEY,
    timepoint_id INTEGER,
    go_terms JSON,
    p_value FLOAT,
    enrichment_score FLOAT,
    source TEXT,
    biologicalProcessCount INTEGER,
    significantBiologicalProcesses JSON,
    topBiologicalProcess TEXT,
    biologicalProcessAnnotationDetails JSON,
    FOREIGN KEY (dmr_id) REFERENCES dmrs(id)
);

-- Create GO Enrichment Biclique Table
CREATE TABLE go_enrichment_biclique (
    biclique_id INTEGER,
    timepoint_id INTEGER,
    go_terms JSON,
    p_value FLOAT,
    enrichment_score FLOAT,
    source TEXT,
    biologicalProcessCount INTEGER,
    significantBiologicalProcesses JSON,
    topBiologicalProcess TEXT,
    biologicalProcessAnnotationDetails JSON,
    PRIMARY KEY (biclique_id, timepoint_id),
    FOREIGN KEY (biclique_id) REFERENCES bicliques(id)
);

-- Create Top GO Processes DMR Table
CREATE TABLE top_go_processes_dmr (
    dmr_id INTEGER,
    timepoint_id INTEGER,
    termId TEXT,
    pValue FLOAT,
    enrichmentScore FLOAT,
    PRIMARY KEY (dmr_id, termId),
    FOREIGN KEY (dmr_id) REFERENCES go_enrichment_dmr(dmr_id)
);

-- Create Top GO Processes Biclique Table
CREATE TABLE top_go_processes_biclique (
    biclique_id INTEGER,
    timepoint_id INTEGER,
    termId TEXT,
    pValue FLOAT,
    enrichmentScore FLOAT,
    PRIMARY KEY (biclique_id, termId),
    FOREIGN KEY (biclique_id) REFERENCES go_enrichment_biclique(biclique_id)
);

-- Create Process Status Table for tracking enrichment processes
CREATE TABLE process_status (
    id SERIAL PRIMARY KEY,
    process_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    timepoint_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (timepoint_id) REFERENCES timepoints(id)
);

-- Create indices for efficient process status lookups
CREATE INDEX idx_process_status_lookup ON process_status(process_type, entity_id, timepoint_id);
CREATE INDEX idx_process_status_type ON process_status(process_type);
CREATE INDEX idx_process_status_type ON process_status(process_type);

-- Create Prompt Logs Table for tracking AI model interactions
CREATE TABLE prompt_logs (
    id SERIAL PRIMARY KEY,
    prompt TEXT NOT NULL,
    prompt_template TEXT,
    model VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    response TEXT,
    tokens_used INTEGER,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    processing_time INTEGER, -- in milliseconds
    status VARCHAR(50) NOT NULL, -- 'success' or 'error'
    error_message TEXT,
    metadata JSONB, -- for additional flexible data storage
    user_feedback TEXT,
    cost DECIMAL(10,6), -- estimated cost in currency units
    
    -- Add constraints
    CHECK (status IN ('success', 'error'))
);

-- Create indices for efficient querying of prompt logs
CREATE INDEX idx_prompt_logs_created_at ON prompt_logs(created_at);
CREATE INDEX idx_prompt_logs_model ON prompt_logs(model);
CREATE INDEX idx_prompt_logs_status ON prompt_logs(status);
CREATE INDEX idx_prompt_logs_tokens ON prompt_logs(tokens_used);

-- Indexing for Performance

-- Indexing for Performance
CREATE INDEX idx_timepoints_name ON timepoints(name);
CREATE INDEX idx_genes_symbol ON genes(symbol);
CREATE INDEX idx_bicliques_timepoint ON bicliques(timepoint_id);
CREATE INDEX idx_bicliques_component ON bicliques(component_id);
CREATE INDEX idx_component_bicliques ON component_bicliques(component_id, biclique_id);
