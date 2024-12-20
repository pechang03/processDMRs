-- DMR Area Analysis Views
CREATE VIEW IF NOT EXISTS v_dmr_area_stats AS
SELECT 
    dmr.timepoint,
    COUNT(*) as dmr_count,
    AVG(dmr.area) as avg_area,
    MIN(dmr.area) as min_area,
    MAX(dmr.area) as max_area,
    SUM(dmr.area) as total_area
FROM dmr
GROUP BY dmr.timepoint;

-- DMR-Gene Association Analysis
CREATE VIEW IF NOT EXISTS v_dmr_gene_coverage AS
SELECT
    d.timepoint,
    COUNT(DISTINCT d.dmr_id) as dmr_count,
    COUNT(DISTINCT g.gene_id) as gene_count,
    COUNT(DISTINCT g.gene_id) * 1.0 / COUNT(DISTINCT d.dmr_id) as genes_per_dmr
FROM dmr d
LEFT JOIN gene g ON d.chr = g.chr 
    AND d.start <= g.end 
    AND d.end >= g.start
GROUP BY d.timepoint;

-- Biclique Participation Analysis
CREATE VIEW IF NOT EXISTS v_biclique_participation AS
SELECT 
    b.timepoint,
    COUNT(DISTINCT b.biclique_id) as biclique_count,
    COUNT(DISTINCT d.dmr_id) as participating_dmrs,
    COUNT(DISTINCT g.gene_id) as participating_genes,
    AVG(d.area) as avg_dmr_area
FROM biclique b
JOIN biclique_dmr bd ON b.biclique_id = bd.biclique_id
JOIN dmr d ON bd.dmr_id = d.dmr_id
JOIN biclique_gene bg ON b.biclique_id = bg.biclique_id
JOIN gene g ON bg.gene_id = g.gene_id
GROUP BY b.timepoint;

-- Biclique Overlap Analysis
CREATE VIEW IF NOT EXISTS v_biclique_overlap AS
WITH dmr_biclique_counts AS (
    SELECT 
        d.dmr_id,
        d.timepoint,
        COUNT(DISTINCT bd.biclique_id) as biclique_count
    FROM dmr d
    JOIN biclique_dmr bd ON d.dmr_id = bd.dmr_id
    GROUP BY d.dmr_id, d.timepoint
)
SELECT
    timepoint,
    AVG(biclique_count) as avg_bicliques_per_dmr,
    MAX(biclique_count) as max_bicliques_per_dmr,
    COUNT(CASE WHEN biclique_count > 1 THEN 1 END) * 100.0 / COUNT(*) as overlap_percentage
FROM dmr_biclique_counts
GROUP BY timepoint;

-- DMR Clustering Analysis
CREATE VIEW IF NOT EXISTS v_dmr_clusters AS
WITH dmr_distances AS (
    SELECT 
        d1.dmr_id as dmr1_id,
        d2.dmr_id as dmr2_id,
        d1.timepoint,
        ABS(d1.start - d2.start) as distance
    FROM dmr d1
    JOIN dmr d2 ON d1.chr = d2.chr 
        AND d1.timepoint = d2.timepoint
        AND d1.dmr_id < d2.dmr_id
        AND ABS(d1.start - d2.start) <= 10000
)
SELECT
    timepoint,
    COUNT(DISTINCT dmr1_id) + COUNT(DISTINCT dmr2_id) as clustered_dmrs,
    AVG(distance) as avg_cluster_distance
FROM dmr_distances
GROUP BY timepoint;

