CREATE OR REPLACE VIEW component_details_view AS
WITH component_dmrs AS (
    SELECT 
        c.id as component_id,
        string_agg(DISTINCT d.unit_id::text, ', ' ORDER BY d.unit_id::text) as dmr_ids,
        COUNT(DISTINCT d.unit_id) as dmr_count
    FROM components c
    JOIN component_dmrs cd ON c.id = cd.component_id
    JOIN dmrs d ON cd.dmr_id = d.id
    GROUP BY c.id
),
component_bicliques AS (
    SELECT 
        c.id as component_id,
        COUNT(DISTINCT b.id) as biclique_count,
        string_agg(DISTINCT b.category, ', ' ORDER BY b.category) as biclique_categories
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

