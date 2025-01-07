-- View for genes with their timepoint annotations
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
LEFT JOIN timepoints t ON gta.timepoint_id = t.id;

-- View for DMRs with their timepoint annotations
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
    dta.timepoint_id,      -- Added from views.sql
    dta.component_id,
    dta.triconnected_id,
    dta.degree,
    dta.node_type,
    dta.is_isolate,
    dta.biclique_ids
FROM dmrs d
LEFT JOIN dmr_timepoint_annotations dta ON d.id = dta.dmr_id
LEFT JOIN timepoints t ON dta.timepoint_id = t.id;

-- Component summary view
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
    COUNT(DISTINCT cb.biclique_id) as biclique_count,
    GROUP_CONCAT(DISTINCT b.category) as biclique_categories
FROM components c
JOIN timepoints t ON c.timepoint_id = t.id
LEFT JOIN component_bicliques cb ON c.id = cb.component_id
LEFT JOIN bicliques b ON cb.biclique_id = b.id
GROUP BY 
    c.id, c.timepoint_id, t.name, c.graph_type, c.category, 
    c.size, c.dmr_count, c.gene_count, c.edge_count, c.density;

-- Component details view with concatenated DMR and gene IDs
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
GROUP BY t.id, t.name, c.id, c.graph_type;

-- Biclique details view
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
JOIN components c ON b.component_id = c.id;

-- Timepoint statistics view
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
GROUP BY t.name;

-- Component node details view
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
GROUP BY c.id, t.name, c.graph_type;

-- Triconnected component view
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
