-- Gene annotations view (basic version without json_each dependencies)
CREATE VIEW IF NOT EXISTS gene_annotations_view AS
SELECT
    g.id AS gene_id,
    g.symbol,
    gta.timepoint_id,
    gta.node_type,
    gta.gene_type,
    gta.degree,
    gta.is_isolate,
    gta.biclique_ids
FROM genes g
JOIN gene_timepoint_annotations gta ON g.id = gta.gene_id;

-- DMR status view (basic version without json_each dependencies)
CREATE VIEW IF NOT EXISTS dmr_status_view AS
SELECT
    d.id AS dmr_id,
    dta.timepoint_id,
    dta.node_type,
    dta.degree,
    dta.is_isolate,
    dta.biclique_ids
FROM dmrs d
JOIN dmr_timepoint_annotations dta ON d.id = dta.dmr_id;

-- Component summary view (simplified)
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
    c.density
FROM components c
JOIN timepoints t ON c.timepoint_id = t.id;

-- Timepoint statistics view (basic version)
CREATE VIEW timepoint_stats_view AS
SELECT
    t.name AS timepoint,
    COUNT(DISTINCT d.id) AS total_dmrs,
    COUNT(DISTINCT g.id) AS total_genes,
    COUNT(DISTINCT CASE WHEN d.is_hub THEN d.id END) AS hub_dmrs,
    COUNT(DISTINCT b.id) AS biclique_count,
    COUNT(DISTINCT c.id) AS component_count
FROM timepoints t
LEFT JOIN dmrs d ON t.id = d.timepoint_id
LEFT JOIN gene_timepoint_annotations gta ON t.id = gta.timepoint_id
LEFT JOIN genes g ON gta.gene_id = g.id
LEFT JOIN bicliques b ON t.id = b.timepoint_id
LEFT JOIN components c ON t.id = c.timepoint_id
GROUP BY t.name;

-- Component nodes view (basic version)
CREATE VIEW component_nodes_view AS
SELECT
    c.id AS component_id,
    t.name AS timepoint,
    c.graph_type
FROM components c
JOIN timepoints t ON c.timepoint_id = t.id;

-- Triconnected component view (basic version)
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
    tc.catagory AS category
FROM triconnected_components tc
JOIN timepoints t ON tc.timepoint_id = t.id
JOIN components c ON tc.component_id = c.id;

CREATE VIEW component_details_view AS
WITH component_dmrs AS (
    SELECT
        c.id AS component_id,
        GROUP_CONCAT(
            DISTINCT d.unit_id, ', '
            ORDER BY d.unit_id)
            AS dmr_ids,
        COUNT(DISTINCT d.unit_id) AS dmr_count
    FROM components c
    JOIN component_dmrs cd ON c.id = cd.component_id
    JOIN dmrs d ON cd.dmr_id = d.id
    GROUP BY c.id
),

component_bicliques AS (
    SELECT
        c.id AS component_id,
        COUNT(DISTINCT b.id) AS biclique_count,
        GROUP_CONCAT(
            DISTINCT b.category, ', '
            ORDER BY b.category)
            AS biclique_categories
    FROM components c
    LEFT JOIN bicliques b ON c.id = b.component_id
    GROUP BY c.id
)

SELECT
    c.id,
    c.timepoint,
    c.graph_type,
    c.category,
    c.size,
    c.density,
    cd.dmr_ids,
    cd.dmr_count,
    cb.biclique_count,
    cb.biclique_categories
FROM components c
LEFT JOIN component_dmrs cd ON c.id = cd.component_id
LEFT JOIN component_bicliques cb ON c.id = cb.component_id
ORDER BY c.id;
