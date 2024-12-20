import React from 'react';
import {
    Box,
    Paper,
    Typography,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Button,
    CircularProgress,
    Alert
} from '@mui/material';

function BicliqueDetailView({ timepointId, timepointDetails }) {
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState(null);

    if (!timepointDetails || !timepointDetails.bicliques) {
        return null;
    }
    
    const stats = timepointDetails.stats;
    
    return (
        <Box sx={{ width: '100%', mt: 3 }}>
            <Paper elevation={3} sx={{ p: 3 }}>
                {/* Component Details Section */}
                <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
                    <Typography variant="h5" gutterBottom>
                        Component Analysis for Timepoint {timepointDetails.bicliques[0].timepoint}
                    </Typography>
                    
                    <TableContainer>
                        <Table size="small">
                            <TableHead>
                                <TableRow>
                                    <TableCell>Component ID</TableCell>
                                    <TableCell align="right">Total Bicliques</TableCell>
                                    <TableCell align="right">Total DMRs</TableCell>
                                    <TableCell align="right">Total Genes</TableCell>
                                    <TableCell>Type</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {Array.from(new Set(timepointDetails.bicliques.map(b => b.component_id))).map((componentId) => {
                                    const componentBicliques = timepointDetails.bicliques.filter(b => b.component_id === componentId);
                                    const totalDMRs = componentBicliques.reduce((sum, b) => sum + (b.dmr_count || 0), 0);
                                    const totalGenes = componentBicliques.reduce((sum, b) => sum + (b.gene_count || 0), 0);
                                    const type = componentBicliques[0].graph_type;
                                    
                                    return (
                                        <TableRow key={componentId}
                                            hover
                                            sx={{ '&:nth-of-type(odd)': { backgroundColor: 'rgba(0, 0, 0, 0.04)' } }}
                                        >
                                            <TableCell>{componentId}</TableCell>
                                            <TableCell align="right">{componentBicliques.length}</TableCell>
                                            <TableCell align="right">{totalDMRs}</TableCell>
                                            <TableCell align="right">{totalGenes}</TableCell>
                                            <TableCell>{type}</TableCell>
                                        </TableRow>
                                    );
                                })}
                            </TableBody>
                        </Table>
                    </TableContainer>
                </Paper>

                {/* Bicliques Section */}
                <Paper elevation={3} sx={{ p: 3 }}>
                    <Typography variant="h5" gutterBottom>
                        Biclique Details
                    </Typography>


                {loading ? (
                    <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                        <CircularProgress />
                    </Box>
                ) : error ? (
                    <Alert severity="error">{error}</Alert>
                ) : (
                    <TableContainer>
                        <Table size="small">
                            <TableHead>
                                <TableRow>
                                    <TableCell>Biclique ID</TableCell>
                                    <TableCell>Category</TableCell>
                                    <TableCell>Component ID</TableCell>
                                    <TableCell>Graph Type</TableCell>
                                    <TableCell align="right">DMR Count</TableCell>
                                    <TableCell align="right">Gene Count</TableCell>
                                    <TableCell>Actions</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {timepointDetails.bicliques.map((biclique) => (
                                    <TableRow key={biclique.biclique_id} 
                                        hover
                                        sx={{ '&:nth-of-type(odd)': { backgroundColor: 'rgba(0, 0, 0, 0.04)' } }}
                                    >
                                        <TableCell>{biclique.biclique_id}</TableCell>
                                        <TableCell>{biclique.category}</TableCell>
                                        <TableCell>{biclique.component_id}</TableCell>
                                        <TableCell>{biclique.graph_type}</TableCell>
                                        <TableCell align="right">{biclique.dmr_count || 0}</TableCell>
                                        <TableCell align="right">{biclique.gene_count || 0}</TableCell>
                                        <TableCell>
                                            <Button
                                                size="small"
                                                variant="outlined"
                                                onClick={() => {
                                                    console.log('View details for biclique:', biclique.biclique_id);
                                                }}
                                            >
                                                View Details
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </TableContainer>
                    )}
                </Paper>
            </Box>
        );
    }

export default BicliqueDetailView;
