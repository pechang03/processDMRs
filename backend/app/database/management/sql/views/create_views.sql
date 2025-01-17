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

CREATE VIEW IF NOT EXISTS component_details_view AS
WITH component_info AS (
    SELECT 
        c.id AS component_id,
        c.timepoint_id,
        t.name AS timepoint,
        c.graph_type,
        c.category,
        c.size,
        c.dmr_count AS total_dmr_count,
        c.gene_count AS total_gene_count,
        (SELECT GROUP_CONCAT(d.id) 
         FROM component_dmrs cd
         JOIN dmrs d ON cd.dmr_id = d.id
         WHERE cd.component_id = c.id) AS all_dmr_ids,
        (SELECT GROUP_CONCAT(g.id)
         FROM component_genes cg
         JOIN genes g ON cg.gene_id = g.id
         WHERE cg.component_id = c.id) AS all_gene_ids
    FROM components c
    JOIN timepoints t ON c.timepoint_id = t.id
),
biclique_info AS (
    SELECT 
        b.id as biclique_id,
        b.dmr_ids,
        b.gene_ids,
        b.category,
        cb.component_id
    FROM bicliques b
    JOIN component_bicliques cb ON b.id = cb.biclique_id
),
dominating_info AS (
    SELECT 
        ds.dmr_id,
        ds.dominated_gene_count,
        ds.utility_score,
        ds.timepoint_id
    FROM dominating_sets ds
)
SELECT 
    ci.*,
    CASE 
        WHEN bi.biclique_id IS NULL THEN '[]'
        ELSE json_group_array(
            json_object(
                'biclique_id', bi.biclique_id,
                'category', bi.category,
                'dmr_ids', bi.dmr_ids,
                'gene_ids', bi.gene_ids
            )
        ) 
    END as bicliques,
    CASE 
        WHEN di.dmr_id IS NULL THEN '[]'
        ELSE json_group_array(
            json_object(
                'dmr_id', di.dmr_id,
                'dominated_gene_count', di.dominated_gene_count,
                'utility_score', di.utility_score
            )
        )
    END as dominating_sets
FROM component_info ci
LEFT JOIN biclique_info bi ON ci.component_id = bi.component_id
LEFT JOIN dominating_info di ON ci.timepoint_id = di.timepoint_id
    AND di.dmr_id IN (
        SELECT CAST(trim(value) AS INTEGER)
        FROM json_each(
            CASE 
                WHEN json_valid(ci.all_dmr_ids)
                THEN ci.all_dmr_ids
                ELSE json_array(ci.all_dmr_ids)
            END
        )
    )
GROUP BY ci.component_id;
