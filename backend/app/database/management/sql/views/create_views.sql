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
    dta.timepoint_id,
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
    COUNT(DISTINCT cb.biclique_id) AS biclique_count,
    GROUP_CONCAT(DISTINCT b.category) AS biclique_categories
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

-- View for component details with bicliques and dominating sets
CREATE VIEW component_details_extended_view AS
WITH component_info AS (
    SELECT 
        cd.timepoint_id,
        cd.timepoint,
        cd.component_id,
        cd.graph_type,
        cd.categories,
        cd.total_dmr_count,
        cd.total_gene_count,
        cd.all_dmr_ids,
        cd.all_gene_ids
    FROM component_details_view cd
),
biclique_info AS (
    SELECT 
        b.id as biclique_id,
        b.dmr_ids,
        b.gene_ids,
        b.category
    FROM bicliques b
    JOIN component_bicliques cb ON b.id = cb.biclique_id
),
dominating_info AS (
    SELECT 
        ds.dmr_id,
        ds.dominated_gene_count,
        ds.utility_score
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
LEFT JOIN biclique_info bi ON 1=1
LEFT JOIN dominating_info di ON 1=1
GROUP BY ci.component_id;

-- View for component genes with biclique counts
CREATE VIEW component_genes_view AS
WITH component_genes AS (
    SELECT DISTINCT
        g.id as gene_id,
        COUNT(DISTINCT cb.biclique_id) as biclique_count
    FROM genes g
    JOIN bicliques b ON instr(',' || b.gene_ids || ',', ',' || g.id || ',') > 0
    JOIN component_bicliques cb ON b.id = cb.biclique_id
    GROUP BY g.id
)
SELECT 
    g.id as gene_id,
    g.symbol,
    gta.node_type,
    gta.gene_type,
    gta.degree,
    gta.is_isolate,
    gta.biclique_ids,
    cg.biclique_count,
    CASE WHEN cg.biclique_count > 1 THEN 1 ELSE 0 END as is_split
FROM component_genes cg
JOIN genes g ON g.id = cg.gene_id
JOIN gene_timepoint_annotations gta ON g.id = gta.gene_id
WHERE gta.timepoint_id = (
    SELECT timepoint_id 
    FROM component_bicliques cb2
    WHERE cb2.biclique_id = cb.biclique_id
    LIMIT 1
);

-- Base component details view
CREATE VIEW IF NOT EXISTS component_details_view AS
WITH 
-- CTE to get all genes associated with components
component_genes AS (
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
    JOIN genes g ON CAST(gene_ids.value AS INTEGER) = g.id
    GROUP BY cb.component_id, cb.timepoint_id, t.name
),
-- CTE to get all DMRs associated with components
component_dmrs AS (
    SELECT 
        cb.component_id,
        cb.timepoint_id,
        GROUP_CONCAT(DISTINCT d.id) as all_dmr_ids,
        COUNT(DISTINCT d.id) as total_dmr_count
    FROM component_bicliques cb
    JOIN bicliques b ON cb.biclique_id = b.id
    JOIN json_each(b.dmr_ids) dmr_ids
    JOIN dmrs d ON CAST(dmr_ids.value AS INTEGER) = d.id
    GROUP BY cb.component_id, cb.timepoint_id
),
-- CTE to get all categories associated with components
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
    gta.timepoint_id,
    gta.node_type,
    gta.gene_type,
    gta.degree,
    gta.is_isolate,
    gta.biclique_ids,
    COUNT(DISTINCT cb.biclique_id) as biclique_count
FROM genes g
JOIN gene_timepoint_annotations gta ON g.id = gta.gene_id
LEFT JOIN component_bicliques cb ON g.id IN (
    SELECT CAST(value AS INTEGER)
    FROM json_each(
        COALESCE(
            (SELECT gene_ids FROM bicliques WHERE id = cb.biclique_id),
            '[]'
        )
    )
)
GROUP BY g.id, g.symbol, gta.timepoint_id, gta.node_type, gta.gene_type, 
         gta.degree, gta.is_isolate, gta.biclique_ids;

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
    SELECT CAST(value AS INTEGER)
    FROM json_each(
        COALESCE(
            (SELECT dmr_ids FROM bicliques WHERE id = cb.biclique_id),
            '[]'
        )
    )
)
GROUP BY d.id, dta.timepoint_id, dta.node_type, dta.degree, dta.is_isolate, dta.biclique_ids;

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
    AVG(COALESCE(CAST(c.density AS FLOAT), 0.0)) AS avg_component_density,
    AVG(COALESCE(CAST(c.size AS FLOAT), 0.0)) AS avg_component_size,
    AVG(COALESCE(CAST(c.dmr_count AS FLOAT), 0.0)) AS avg_dmr_count,
    AVG(COALESCE(CAST(c.gene_count AS FLOAT), 0.0)) AS avg_gene_count
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
