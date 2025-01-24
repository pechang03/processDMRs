DROP VIEW IF EXISTS gene_annotations_view;
CREATE VIEW gene_annotations_view AS
SELECT
    g.id AS gene_id,
    g.master_gene_id,
    g.symbol,
    g.description,
    g.chromosome,
    g.start_position,
    g.end_position,
    g.strand,
    g.gene_type,
    g.created_at,
    g.updated_at,
    gta.timepoint_id,
    gta.node_type,
    gta.degree,
    gta.is_isolate,
    gta.biclique_ids,
    gta.component_id
FROM genes g
JOIN gene_timepoint_annotations gta ON g.id = gta.gene_id;

DROP VIEW IF EXISTS dmr_annotations_view;
CREATE VIEW dmr_annotations_view AS
SELECT
    d.id AS dmr_id,
    d.area_stat,
    d.chromosome,
    d.start_position,
    d.end_position,
    COALESCE(d.mean_methylation, 0.0) AS methylation_difference,
    d.p_value,
    d.q_value,
    dta.timepoint_id,
    CASE
        WHEN d.is_hub THEN 'hub'
        ELSE 'regular'
    END AS node_type,  -- Direct classification
    dta.degree,  -- Get pre-calculated degree from annotations table
    dta.is_isolate,
    dta.biclique_ids,
    dta.component_id,
    t.name AS timepoint_name
FROM dmrs d
JOIN dmr_timepoint_annotations dta ON d.id = dta.dmr_id
JOIN timepoints t ON dta.timepoint_id = t.id;

DROP VIEW IF EXISTS component_summary_view;
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
    COUNT(DISTINCT b.id) AS biclique_count,
    GROUP_CONCAT(DISTINCT b.category) AS biclique_categories
FROM components c
JOIN timepoints t ON c.timepoint_id = t.id
LEFT JOIN bicliques b ON c.id = b.component_id
GROUP BY c.id;

DROP VIEW IF EXISTS component_details_view;
CREATE VIEW component_details_view AS
SELECT
    t.id AS timepoint_id,
    t.name AS timepoint,
    c.id AS component_id,
    c.graph_type,
    COALESCE(GROUP_CONCAT(DISTINCT b.category), '') AS categories,
    COALESCE(SUM(JSON_ARRAY_LENGTH(b.dmr_ids)), 0) AS total_dmr_count,
    COALESCE(SUM(JSON_ARRAY_LENGTH(b.gene_ids)), 0) AS total_gene_count,
    COALESCE(
        (
            SELECT JSON_GROUP_ARRAY(DISTINCT value)
            FROM bicliques b2, JSON_EACH(b2.dmr_ids)
            WHERE b2.component_id = c.id AND b2.timepoint_id = t.id
        ),
        '[]'
    ) AS all_dmr_ids,
    COALESCE(
        (
            SELECT JSON_GROUP_ARRAY(DISTINCT value)
            FROM bicliques b3, JSON_EACH(b3.gene_ids)
            WHERE b3.component_id = c.id AND b3.timepoint_id = t.id
        ),
        '[]'
    ) AS all_gene_ids
FROM components c
JOIN timepoints t ON c.timepoint_id = t.id
LEFT JOIN bicliques b ON b.component_id = c.id AND b.timepoint_id = t.id
GROUP BY t.id, t.name, c.id, c.graph_type;

DROP VIEW IF EXISTS biclique_details_view_old;
CREATE VIEW biclique_details_view AS
SELECT
    b.id AS biclique_id,
    b.timepoint_id,
    t.name AS timepoint,
    b.component_id,
    b.graph_type,
    b.category,
    b.dmr_ids,
    b.gene_ids,
    JSON_ARRAY_LENGTH(b.dmr_ids) AS dmr_count,
    JSON_ARRAY_LENGTH(b.gene_ids) AS gene_count
FROM bicliques b
JOIN timepoints t ON b.timepoint_id = t.id;

DROP VIEW IF EXISTS timepoint_stats_view;
CREATE VIEW timepoint_stats_view AS
SELECT
    t.name AS timepoint,
    COUNT(DISTINCT d.id) AS total_dmrs,
    COUNT(DISTINCT g.id) AS total_genes,
    COUNT(DISTINCT CASE WHEN dta.node_type = 'hub' THEN d.id END) AS hub_dmrs,
    COUNT(DISTINCT CASE WHEN gta.node_type = 'hub' THEN g.id END) AS hub_genes,
    COUNT(DISTINCT b.id) AS biclique_count,
    COUNT(DISTINCT c.id) AS component_count,
    AVG(c.density) AS avg_component_density
FROM timepoints t
LEFT JOIN dmr_timepoint_annotations dta ON t.id = dta.timepoint_id
LEFT JOIN dmrs d ON dta.dmr_id = d.id
LEFT JOIN gene_timepoint_annotations gta ON t.id = gta.timepoint_id
LEFT JOIN genes g ON gta.gene_id = g.id
LEFT JOIN bicliques b ON t.id = b.timepoint_id
LEFT JOIN components c ON t.id = c.timepoint_id
GROUP BY t.name;

DROP VIEW IF EXISTS component_nodes_view;
CREATE VIEW component_nodes_view AS
SELECT
    c.id AS component_id,
    t.name AS timepoint,
    c.graph_type,
    JSON_GROUP_ARRAY(
        JSON_OBJECT(
            'id', d.id,
            'type', 'dmr',
            'chromosome', d.chromosome,
            'start', d.start_position,
            'end', d.end_position,
            'node_type', dta.node_type
        )
    ) AS dmr_nodes,
    JSON_GROUP_ARRAY(
        JSON_OBJECT(
            'id', g.id,
            'type', 'gene',
            'symbol', g.symbol,
            'chromosome', g.chromosome,
            'start', g.start_position,
            'end', g.end_position,
            'node_type', gta.node_type
        )
    ) AS gene_nodes
FROM components c
JOIN timepoints t ON c.timepoint_id = t.id
LEFT JOIN dmr_timepoint_annotations dta ON c.id = dta.component_id
LEFT JOIN dmrs d ON dta.dmr_id = d.id
LEFT JOIN gene_timepoint_annotations gta ON c.id = gta.component_id
LEFT JOIN genes g ON gta.gene_id = g.id
GROUP BY c.id;

DROP VIEW IF EXISTS triconnected_component_view;
CREATE VIEW triconnected_component_view AS
SELECT
    tc.id AS triconnected_id,
    tc.timepoint_id,
    t.name AS timepoint,
    tc.component_id,
    tc.size,
    tc.dmr_count,
    tc.gene_count,
    tc.edge_count,
    tc.density,
    tc.category,
    tc.separation_pair_1,
    tc.separation_pair_2,
    tc.parent_id
FROM triconnected_components tc
JOIN timepoints t ON tc.timepoint_id = t.id;
