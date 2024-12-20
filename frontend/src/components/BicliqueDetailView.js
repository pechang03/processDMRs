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

    if (!timepointDetails || !timepointDetails.components) {
        return null;
    }
    
    const stats = timepointDetails.stats;
    
    return (
        <Box sx={{ width: '100%', mt: 3 }}>
            <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
                <Typography variant="h5" gutterBottom>
                    Component Analysis for Timepoint {timepointDetails.timepoint}
                </Typography>
                
                <Box sx={{ mb: 3 }}>
                    <Typography variant="h6" gutterBottom>Statistics Summary</Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                        {stats && Object.entries(stats).map(([key, value]) => (
                            <Typography key={key} variant="body1">
                                {key.replace(/([A-Z])/g, ' $1').trim()}: <b>{value}</b>
                            </Typography>
                        ))}
                    </Box>
                </Box>
                    <TableContainer>
                        <Table size="small">
                            <TableHead>
                                <TableRow>
                                    <TableCell>Component ID</TableCell>
                                    <TableCell>Category</TableCell>
                                    <TableCell>Type</TableCell>
                                    <TableCell align="right">DMR Count</TableCell>
                                    <TableCell align="right">Gene Count</TableCell>
                                    <TableCell>DMR IDs</TableCell>
                                    <TableCell>Gene Symbols</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {timepointDetails.components.map((component) => (
                                    <TableRow key={component.component_id}
                                        hover
                                        sx={{ '&:nth-of-type(odd)': { backgroundColor: 'rgba(0, 0, 0, 0.04)' } }}
                                    >
                                        <TableCell>{component.component_id}</TableCell>
                                        <TableCell>{component.category}</TableCell>
                                        <TableCell>{component.graph_type}</TableCell>
                                        <TableCell align="right">{component.dmr_count || 0}</TableCell>
                                        <TableCell align="right">{component.gene_count || 0}</TableCell>
                                        <TableCell>
                                            <Typography
                                                sx={{
                                                    maxWidth: 300,
                                                    overflow: 'hidden',
                                                    textOverflow: 'ellipsis',
                                                    whiteSpace: 'nowrap',
                                                    fontFamily: 'monospace',
                                                    fontSize: '0.875rem'
                                                }}
                                                title={Array.isArray(component.all_dmr_ids) ? component.all_dmr_ids.join(', ') : component.all_dmr_ids}>
                                                {Array.isArray(component.all_dmr_ids) ? component.all_dmr_ids.join(', ') : component.all_dmr_ids}
                                            </Typography>
                                        </TableCell>
                                        <TableCell>
                                            <Typography
                                                sx={{
                                                    maxWidth: 300,
                                                    overflow: 'hidden',
                                                    textOverflow: 'ellipsis',
                                                    whiteSpace: 'nowrap',
                                                    fontFamily: 'monospace',
                                                    fontSize: '0.875rem',
                                                    color: 'primary.main'
                                                }}
                                                title={Array.isArray(component.gene_symbols) ? component.gene_symbols.join(', ') : component.gene_symbols}>
                                                {Array.isArray(component.gene_symbols) ? component.gene_symbols.join(', ') : component.gene_symbols}
                                            </Typography>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </TableContainer>
                </Paper>
            </Box>
        );
    }

export default BicliqueDetailView;
