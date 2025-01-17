-- Base component details view
CREATE VIEW IF NOT EXISTS component_details_view AS
WITH component_genes AS (
    SELECT 
        cb.component_id,
        cb.timepoint_id,
        t.name as timepoint,
        GROUP_CONCAT(DISTINCT g.id) as all_gene_ids,
        COUNT(DISTINCT g.id) as total_gene_count
    FROM component_bicliques cb
    JOIN timepoints t ON cb.timepoint_id = t.id
    JOIN bicliques b ON cb.biclique_id = b.id
    JOIN json_each(b.gene_ids) gene_ids
    JOIN genes g ON gene_ids.value = g.id
    GROUP BY cb.component_id, cb.timepoint_id, t.name
),
component_dmrs AS (
    SELECT 
        cb.component_id,
        cb.timepoint_id,
        GROUP_CONCAT(DISTINCT d.id) as all_dmr_ids,
        COUNT(DISTINCT d.id) as total_dmr_count
    FROM component_bicliques cb
    JOIN bicliques b ON cb.biclique_id = b.id
    JOIN json_each(b.dmr_ids) dmr_ids
    JOIN dmrs d ON dmr_ids.value = d.id
    GROUP BY cb.component_id, cb.timepoint_id
),
component_categories AS (
    SELECT 
        cb.component_id,
        cb.timepoint_id,
        GROUP_CONCAT(DISTINCT b.category) as categories
    FROM component_bicliques cb
    JOIN bicliques b ON cb.biclique_id = b.id
    GROUP BY cb.component_id, cb.timepoint_id
)
SELECT 
    c.id as component_id,
    c.timepoint_id,
    cg.timepoint,
    c.graph_type,
    cc.categories,
    cd.total_dmr_count,
    cg.total_gene_count,
    cd.all_dmr_ids,
    cg.all_gene_ids
FROM components c
LEFT JOIN component_genes cg ON c.id = cg.component_id AND c.timepoint_id = cg.timepoint_id
LEFT JOIN component_dmrs cd ON c.id = cd.component_id AND c.timepoint_id = cd.timepoint_id
LEFT JOIN component_categories cc ON c.id = cc.component_id AND c.timepoint_id = cc.timepoint_id;

-- Gene annotations view
CREATE VIEW IF NOT EXISTS gene_annotations_view AS
SELECT 
    g.id as gene_id,
    g.symbol,
    gta.node_type,
    gta.gene_type,
    gta.degree,
    gta.is_isolate,
    gta.biclique_ids,
    COUNT(DISTINCT cb.biclique_id) as biclique_count
FROM genes g
JOIN gene_timepoint_annotations gta ON g.id = gta.gene_id
LEFT JOIN component_bicliques cb ON g.id IN (
    SELECT value
    FROM json_each((SELECT gene_ids FROM bicliques WHERE id = cb.biclique_id))
)
GROUP BY g.id, g.symbol, gta.node_type, gta.gene_type, gta.degree, gta.is_isolate, gta.biclique_ids;

-- DMR status view
CREATE VIEW IF NOT EXISTS dmr_status_view AS
SELECT 
    d.id as dmr_id,
    dta.timepoint_id,
    dta.node_type,
    dta.degree,
    dta.is_isolate,
    dta.biclique_ids,
    COUNT(DISTINCT cb.biclique_id) as biclique_count
FROM dmrs d
JOIN dmr_timepoint_annotations dta ON d.id = dta.dmr_id
LEFT JOIN component_bicliques cb ON d.id IN (
    SELECT value
    FROM json_each((SELECT dmr_ids FROM bicliques WHERE id = cb.biclique_id))
)
GROUP BY d.id, dta.timepoint_id, dta.node_type, dta.degree, dta.is_isolate, dta.biclique_ids;

