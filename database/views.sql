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
    dta.component_id,
    dta.triconnected_id,
    dta.degree,
    dta.node_type,
    dta.is_isolate,
    dta.biclique_ids
FROM dmrs d
LEFT JOIN dmr_timepoint_annotations dta ON d.id = dta.dmr_id
LEFT JOIN timepoints t ON dta.timepoint_id = t.id;
