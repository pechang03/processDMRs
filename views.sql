CREATE TABLE timepoints(
  id INTEGER NOT NULL,
  name VARCHAR(255) NOT NULL,
  sheet_name VARCHAR(255) NOT NULL,
  description TEXT,
  dmr_id_offset INTEGER,
  PRIMARY KEY(id),
  UNIQUE(name),
  UNIQUE(sheet_name)
);
CREATE TABLE master_gene_ids(
  id INTEGER NOT NULL,
  gene_symbol VARCHAR(255) NOT NULL,
  PRIMARY KEY(id)
);
CREATE UNIQUE INDEX ix_master_gene_ids_gene_symbol_lower ON master_gene_ids(
  lower(gene_symbol)
);
CREATE TABLE statistics(
  id INTEGER NOT NULL,
  category VARCHAR(50),
  "key" VARCHAR(255),
  value TEXT,
  PRIMARY KEY(id)
);
CREATE TABLE relationships(
  id INTEGER NOT NULL,
  source_entity_type VARCHAR(50),
  source_entity_id INTEGER,
  target_entity_type VARCHAR(50),
  target_entity_id INTEGER,
  relationship_type VARCHAR(50),
  PRIMARY KEY(id)
);
CREATE TABLE genes(
  id INTEGER NOT NULL,
  symbol VARCHAR(255) NOT NULL,
  description TEXT,
  master_gene_id INTEGER,
  interaction_source VARCHAR(30),
  promoter_info VARCHAR(30),
  PRIMARY KEY(id),
  UNIQUE(symbol),
  FOREIGN KEY(master_gene_id) REFERENCES master_gene_ids(id)
);
CREATE TABLE dmrs(
  timepoint_id INTEGER,
  id INTEGER NOT NULL,
  dmr_number INTEGER NOT NULL,
  area_stat FLOAT,
  description TEXT,
  dmr_name VARCHAR(255),
  gene_description TEXT,
  chromosome VARCHAR(50),
  start_position INTEGER,
  end_position INTEGER,
  strand VARCHAR(1),
  p_value FLOAT,
  q_value FLOAT,
  mean_methylation FLOAT,
  is_hub BOOLEAN,
  PRIMARY KEY(id),
  CONSTRAINT uq_dmrs_timepoint_dmr UNIQUE(timepoint_id, dmr_number),
  FOREIGN KEY(timepoint_id) REFERENCES timepoints(id)
);
CREATE TABLE components(
  id INTEGER NOT NULL,
  timepoint_id INTEGER,
  graph_type VARCHAR(50) NOT NULL,
  category VARCHAR(50),
  size INTEGER,
  dmr_count INTEGER,
  gene_count INTEGER,
  edge_count INTEGER,
  density FLOAT,
  endcoding VARCHAR(255),
  PRIMARY KEY(id),
  FOREIGN KEY(timepoint_id) REFERENCES timepoints(id)
);
CREATE TABLE bicliques(
  id INTEGER NOT NULL,
  timepoint_id INTEGER,
  component_id INTEGER,
  category VARCHAR(50),
  encoding VARCHAR(255),
  dmr_ids TEXT,
  gene_ids TEXT,
  PRIMARY KEY(id),
  FOREIGN KEY(timepoint_id) REFERENCES timepoints(id),
  FOREIGN KEY(component_id) REFERENCES components(id)
);
CREATE TABLE triconnected_components(
  id INTEGER NOT NULL,
  timepoint_id INTEGER,
  component_id INTEGER,
  dmr_ids TEXT,
  gene_ids TEXT,
  category VARCHAR(50),
  endcoding VARCHAR(255),
  size INTEGER,
  dmr_count INTEGER,
  gene_count INTEGER,
  edge_count INTEGER,
  density FLOAT,
  is_simple BOOLEAN,
  nodes TEXT,
  separation_pairs TEXT,
  avg_dmrs FLOAT,
  avg_genes FLOAT,
  PRIMARY KEY(id),
  FOREIGN KEY(timepoint_id) REFERENCES timepoints(id),
  FOREIGN KEY(component_id) REFERENCES components(id)
);
CREATE TABLE dominating_sets(
  timepoint_id INTEGER NOT NULL,
  dmr_id INTEGER NOT NULL,
  area_stat FLOAT,
  utility_score FLOAT,
  dominated_gene_count INTEGER,
  calculation_timestamp DATETIME,
  PRIMARY KEY(timepoint_id, dmr_id),
  FOREIGN KEY(timepoint_id) REFERENCES timepoints(id),
  FOREIGN KEY(dmr_id) REFERENCES dmrs(id)
);
CREATE TABLE gene_timepoint_annotations(
  timepoint_id INTEGER NOT NULL,
  gene_id INTEGER NOT NULL,
  component_id INTEGER,
  triconnected_id INTEGER,
  degree INTEGER,
  node_type VARCHAR(30),
  gene_type VARCHAR(30),
  is_isolate BOOLEAN,
  biclique_ids TEXT,
  PRIMARY KEY(timepoint_id, gene_id),
  FOREIGN KEY(timepoint_id) REFERENCES timepoints(id),
  FOREIGN KEY(gene_id) REFERENCES genes(id),
  FOREIGN KEY(component_id) REFERENCES components(id),
  FOREIGN KEY(triconnected_id) REFERENCES triconnected_components(id)
);
CREATE TABLE dmr_timepoint_annotations(
  timepoint_id INTEGER NOT NULL,
  dmr_id INTEGER NOT NULL,
  component_id INTEGER,
  triconnected_id INTEGER,
  degree INTEGER,
  node_type VARCHAR(30),
  gene_type VARCHAR(30),
  is_isolate BOOLEAN,
  biclique_ids TEXT,
  PRIMARY KEY(timepoint_id, dmr_id),
  FOREIGN KEY(timepoint_id) REFERENCES timepoints(id),
  FOREIGN KEY(dmr_id) REFERENCES dmrs(id),
  FOREIGN KEY(component_id) REFERENCES components(id),
  FOREIGN KEY(triconnected_id) REFERENCES triconnected_components(id)
);
CREATE TABLE metadata(
  id INTEGER NOT NULL,
  entity_type VARCHAR(50),
  entity_id INTEGER,
  "key" VARCHAR(255),
  value TEXT,
  PRIMARY KEY(id),
  FOREIGN KEY(entity_id) REFERENCES bicliques(id)
);
CREATE TABLE component_bicliques(
  timepoint_id INTEGER NOT NULL,
  component_id INTEGER NOT NULL,
  biclique_id INTEGER NOT NULL,
  PRIMARY KEY(timepoint_id, component_id, biclique_id),
  FOREIGN KEY(timepoint_id) REFERENCES timepoints(id),
  FOREIGN KEY(component_id) REFERENCES components(id),
  FOREIGN KEY(biclique_id) REFERENCES bicliques(id)
);
CREATE VIEW gene_annotations_view AS
SELECT
    g.id AS gene_id,
    g.symbol,
    g.description,
    g.master_gene_id,
    g.interaction_source,
    g.promoter_info,
    t.name AS timepoint,
    gta.timepoint_id,      -- Added from views.sql
    gta.component_id,
    gta.triconnected_id,
    gta.degree,
    gta.node_type,
    gta.gene_type,
    gta.is_isolate,
    gta.biclique_ids
FROM genes g
LEFT JOIN gene_timepoint_annotations gta ON g.id = gta.gene_id
LEFT JOIN timepoints t ON gta.timepoint_id = t.id
/* gene_annotations_view(gene_id,symbol,description,master_gene_id,interaction_source,promoter_info,timepoint,timepoint_id,component_id,triconnected_id,degree,node_type,gene_type,is_isolate,biclique_ids) */;
CREATE VIEW dmr_annotations_view AS
SELECT
    d.id AS dmr_id,
    d.dmr_number,
    d.area_stat,
    d.description,
    d.dmr_name,
    d.gene_description,
    d.chromosome,
    d.start_position,
    d.end_position,
    d.strand,
    d.p_value,
    d.q_value,
    d.mean_methylation,
    d.is_hub,
    t.name AS timepoint,
    dta.timepoint_id,
    dta.component_id,
    dta.triconnected_id,
    dta.degree,
    dta.node_type,
    dta.is_isolate,
    dta.biclique_ids
FROM dmrs d
LEFT JOIN dmr_timepoint_annotations dta ON d.id = dta.dmr_id
LEFT JOIN timepoints t ON dta.timepoint_id = t.id
/* dmr_annotations_view(dmr_id,dmr_number,area_stat,description,dmr_name,gene_description,chromosome,start_position,end_position,strand,p_value,q_value,mean_methylation,is_hub,timepoint,timepoint_id,component_id,triconnected_id,degree,node_type,is_isolate,biclique_ids) */;
CREATE VIEW component_summary_view AS
SELECT
    c.id AS component_id,
    c.timepoint_id,
    t.name AS timepoint,
    c.graph_type,
    c.category,
    c.size,
    c.dmr_count,
    c.gene_count,
    c.edge_count,
    c.density,
    COUNT(DISTINCT cb.biclique_id) AS biclique_count,
    GROUP_CONCAT(DISTINCT b.category) AS biclique_categories
FROM components c
JOIN timepoints t ON c.timepoint_id = t.id
LEFT JOIN component_bicliques cb ON c.id = cb.component_id
LEFT JOIN bicliques b ON cb.biclique_id = b.id
GROUP BY
    c.id, c.timepoint_id, t.name, c.graph_type, c.category,
    c.size, c.dmr_count, c.gene_count, c.edge_count, c.density
/* component_summary_view(component_id,timepoint_id,timepoint,graph_type,category,size,dmr_count,gene_count,edge_count,density,biclique_count,biclique_categories) */;
CREATE VIEW component_details_view AS
SELECT
    t.id AS timepoint_id,
    t.name AS timepoint,
    c.id AS component_id,
    c.graph_type,
    GROUP_CONCAT(DISTINCT b.category) AS categories,
    SUM(LENGTH(b.dmr_ids) - LENGTH(REPLACE(b.dmr_ids, ',', '')) + 1)
        AS total_dmr_count,
    SUM(LENGTH(b.gene_ids) - LENGTH(REPLACE(b.gene_ids, ',', '')) + 1)
        AS total_gene_count,
    GROUP_CONCAT(DISTINCT b.dmr_ids) AS all_dmr_ids,
    GROUP_CONCAT(DISTINCT b.gene_ids) AS all_gene_ids
FROM bicliques b
JOIN timepoints t ON b.timepoint_id = t.id
JOIN components c ON b.component_id = c.id
WHERE b.category != 'simple'
GROUP BY t.id, t.name, c.id, c.graph_type
/* component_details_view(timepoint_id,timepoint,component_id,graph_type,categories,total_dmr_count,total_gene_count,all_dmr_ids,all_gene_ids) */;
CREATE VIEW biclique_details_view AS
SELECT
    b.id AS biclique_id,
    t.id AS timepoint_id,
    t.name AS timepoint,
    b.category,
    c.id AS component_id,
    c.graph_type,
    LENGTH(b.dmr_ids) - LENGTH(REPLACE(b.dmr_ids, ',', '')) + 1 AS dmr_count,
    LENGTH(b.gene_ids) - LENGTH(REPLACE(b.gene_ids, ',', '')) + 1 AS gene_count,
    b.dmr_ids,
    b.gene_ids
FROM bicliques b
JOIN timepoints t ON b.timepoint_id = t.id
JOIN components c ON b.component_id = c.id
/* biclique_details_view(biclique_id,timepoint_id,timepoint,category,component_id,graph_type,dmr_count,gene_count,dmr_ids,gene_ids) */;
CREATE VIEW timepoint_stats_view AS
SELECT
    t.name AS timepoint,
    COUNT(DISTINCT d.id) AS total_dmrs,
    COUNT(DISTINCT g.id) AS total_genes,
    COUNT(DISTINCT CASE WHEN d.is_hub THEN d.id END) AS hub_dmrs,
    COUNT(DISTINCT b.id) AS biclique_count,
    COUNT(DISTINCT c.id) AS component_count,
    AVG(COALESCE(CAST(c.density AS FLOAT), 0)) AS avg_component_density,
    AVG(COALESCE(CAST(c.size AS FLOAT), 0)) AS avg_component_size,
    AVG(COALESCE(CAST(c.dmr_count AS FLOAT), 0)) AS avg_dmr_count,
    AVG(COALESCE(CAST(c.gene_count AS FLOAT), 0)) AS avg_gene_count
FROM timepoints t
LEFT JOIN dmrs d ON t.id = d.timepoint_id
LEFT JOIN gene_timepoint_annotations gta ON t.id = gta.timepoint_id
LEFT JOIN genes g ON gta.gene_id = g.id
LEFT JOIN bicliques b ON t.id = b.timepoint_id
LEFT JOIN components c ON t.id = c.timepoint_id
GROUP BY t.name
/* timepoint_stats_view(timepoint,total_dmrs,total_genes,hub_dmrs,biclique_count,component_count,avg_component_density,avg_component_size,avg_dmr_count,avg_gene_count) */;
CREATE VIEW component_nodes_view AS
SELECT
    c.id AS component_id,
    t.name AS timepoint,
    c.graph_type,
    GROUP_CONCAT(DISTINCT JSON_OBJECT(
        'dmr_id', d.id,
        'dmr_number', d.dmr_number,
        'area_stat', d.area_stat,
        'is_hub', d.is_hub
    )) AS dmrs,
    GROUP_CONCAT(DISTINCT JSON_OBJECT(
        'gene_id', g.id,
        'symbol', g.symbol,
        'interaction_source', g.interaction_source
    )) AS genes
FROM components c
JOIN timepoints t ON c.timepoint_id = t.id
LEFT JOIN dmr_timepoint_annotations dta ON c.id = dta.component_id
LEFT JOIN dmrs d ON dta.dmr_id = d.id
LEFT JOIN gene_timepoint_annotations gta ON c.id = gta.component_id
LEFT JOIN genes g ON gta.gene_id = g.id
GROUP BY c.id, t.name, c.graph_type
/* component_nodes_view(component_id,timepoint,graph_type,dmrs,genes) */;
CREATE VIEW triconnected_component_view AS
SELECT
    tc.id AS triconnected_id,
    t.name AS timepoint,
    c.id AS component_id,
    tc.size,
    tc.dmr_count,
    tc.gene_count,
    tc.edge_count,
    tc.density,
    tc.catagory AS category,
    tc.nodes,
    tc.separation_pairs,
    tc.avg_dmrs,
    tc.avg_genes
FROM triconnected_components tc
JOIN timepoints t ON tc.timepoint_id = t.id
JOIN components c ON tc.component_id = c.id;
