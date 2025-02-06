CREATE OR REPLACE VIEW component_details_view AS
SELECT
    t.id AS timepoint_id,
    t.name AS timepoint,
    c.id AS component_id,
    c.graph_type,
    COALESCE(GROUP_CONCAT(DISTINCT b.category), '') AS categories,
    COALESCE(
        SUM(LENGTH(b.dmr_ids) - LENGTH(REPLACE(b.dmr_ids, ',', '')) + 1), 0
    ) AS total_dmr_count,
    COALESCE(
        SUM(LENGTH(b.gene_ids) - LENGTH(REPLACE(b.gene_ids, ',', '')) + 1), 0
    ) AS total_gene_count,
    COALESCE(GROUP_CONCAT(DISTINCT b.dmr_ids), '') AS all_dmr_ids,
    COALESCE(GROUP_CONCAT(DISTINCT b.gene_ids), '') AS all_gene_ids
FROM components c
JOIN timepoints t ON c.timepoint_id = t.id
LEFT JOIN bicliques b ON b.component_id = c.id
GROUP BY t.id, t.name, c.id, c.graph_type;
