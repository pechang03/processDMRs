DROP VIEW IF EXISTS component_details_view;
CREATE VIEW component_details_view AS
SELECT
    t.id AS timepoint_id,
    t.name AS timepoint,
    c.id AS component_id,
    c.graph_type,
    GROUP_CONCAT(DISTINCT b.category) as categories,
    SUM(length(b.dmr_ids) - length(replace(b.dmr_ids, ',', '')) + 1) as total_dmr_count,
    SUM(length(b.gene_ids) - length(replace(b.gene_ids, ',', '')) + 1) as total_gene_count,
    GROUP_CONCAT(DISTINCT b.dmr_ids) as all_dmr_ids,
    GROUP_CONCAT(DISTINCT b.gene_ids) as all_gene_ids
FROM bicliques b
JOIN timepoints t ON b.timepoint_id = t.id
JOIN components c ON b.component_id = c.id
WHERE b.category != 'simple'
GROUP BY t.id, t.name, c.id, c.graph_type;

