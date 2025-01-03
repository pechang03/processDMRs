import React, { useState, useEffect } from 'react';
import { 
    Paper,
    Typography,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Button,
    Box,
    CircularProgress
} from '@mui/material';

function ComponentsView({ selectedTimepoint, onSelectComponent }) {
    const [components, setComponents] = useState([]);
    const [timepointName, setTimepointName] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (selectedTimepoint) {
            setLoading(true);
            setError(null);
            
            fetch(`/api/components/${selectedTimepoint}/summary`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.status === 'success') {
                        // Ensure we're mapping the correct fields from the backend response
                        setComponents(data.data.map(component => ({
                            component_id: component.component_id,
                            biclique_count: component.biclique_count,
                            gene_count: component.gene_count,
                            dmr_count: component.dmr_count
                        })));
                        setTimepointName(data.timepoint);
                    } else {
                        throw new Error(data.message || 'Failed to fetch components');
                    }
                })
                .catch(error => {
                    console.error('Error fetching components:', error);
                    setError(error.message);
                })
                .finally(() => {
                    setLoading(false);
                });
        }
    }, [selectedTimepoint]);

    if (loading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
                <CircularProgress />
            </Box>
        );
    }

    if (error) {
        return (
            <Box sx={{ p: 2 }}>
                <Typography color="error">Error: {error}</Typography>
            </Box>
        );
    }

    return (
        <Box sx={{ mt: 2 }}>
            <Paper elevation={3} sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                    Components for Timepoint: {timepointName}
                </Typography>
                <TableContainer>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell>Component ID</TableCell>
                                <TableCell align="right">Bicliques</TableCell>
                                <TableCell align="right">Genes</TableCell>
                                <TableCell align="right">DMRs</TableCell>
                                <TableCell>Actions</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {components.map((component) => (
                                <TableRow key={component.component_id}>
                                    <TableCell>{component.component_id}</TableCell>
                                    <TableCell align="right">{component.biclique_count}</TableCell>
                                    <TableCell align="right">{component.gene_count}</TableCell>
                                    <TableCell align="right">{component.dmr_count}</TableCell>
                                    <TableCell>
                                        <Button
                                            variant="contained"
                                            color="primary"
                                            onClick={() => onSelectComponent(component.component_id)}
                                        >
                                            Details
                                        </Button>
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

export default ComponentsView;

