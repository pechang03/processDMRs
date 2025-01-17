
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
    c.timepoint_id,
    t.name AS timepoint,
    c.graph_type,
    c.category,
    c.size,
    c.density,
    cd.dmr_ids,
    cd.dmr_count,
    cb.biclique_count,
    cb.biclique_categories
FROM components c
JOIN timepoints t ON c.timepoint_id = t.id
LEFT JOIN component_dmrs cd ON c.id = cd.component_id
LEFT JOIN component_bicliques cb ON c.id = cb.component_id
ORDER BY c.id;
