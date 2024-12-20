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
                <Typography variant="h5" gutterBottom>
                    Biclique Analysis for Timepoint {timepointDetails.bicliques[0].timepoint}
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
