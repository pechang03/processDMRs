-- Add genome column to gene_details table
ALTER TABLE gene_details ADD COLUMN genome VARCHAR(50) NOT NULL DEFAULT 'mouse';

-- Add check constraint to ensure only valid values
ALTER TABLE gene_details ADD CONSTRAINT chk_genome_values CHECK (genome IN ('mouse', 'human'));

-- Create index on genome column
CREATE INDEX idx_gene_details_genome ON gene_details(genome);

