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
import { API_BASE_URL } from '../config.js';

function ComponentsView({ selectedTimepoint, onSelectComponent }) {
    const [components, setComponents] = useState([]);
    const [timepointName, setTimepointName] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (selectedTimepoint) {
            setLoading(true);
            setError(null);
            
            console.log(`Fetching components for timepoint ${selectedTimepoint}`);
            
            fetch(`${API_BASE_URL}/component/components/${selectedTimepoint}/summary`)
                .then(response => {
                    if (!response.ok) {
                        if (response.status === 404) {
                            throw new Error(`No components found for timepoint ${selectedTimepoint}`);
                        }
                        throw new Error(`Network response was not ok (${response.status}): ${response.statusText}`);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('Received data:', data);
                    
                    if (data.status === 'success') {
                        console.log(`Found ${data.data.length} components`);
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
                    setError(`${error.message} (${error.name})`);
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
                <Alert severity="error">
                    {error.includes('No components found') ? 
                        `No components available for selected timepoint` :
                        error
                    }
                </Alert>
            </Box>
        );
    }

    return (
        <Box sx={{ mt: 2 }}>
            <Paper elevation={3} sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                    Components for Timepoint: {timepointName}
                </Typography>
                {components.length > 0 && (
                    <Typography variant="subtitle1" gutterBottom>
                        Found {components.length} components
                    </Typography>
                )}
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
                                    <TableCell align="right">
                                        {component.biclique_count}
                                        {component.biclique_count <= 1 && (
                                            <Typography 
                                                variant="caption" 
                                                color="text.secondary" 
                                                display="block"
                                            >
                                                (Simple)
                                            </Typography>
                                        )}
                                    </TableCell>
                                    <TableCell align="right">{component.gene_count}</TableCell>
                                    <TableCell align="right">{component.dmr_count}</TableCell>
                                    <TableCell>
                                        <Button
                                            variant="contained"
                                            color="primary"
                                            onClick={() => onSelectComponent(component.component_id)}
                                            disabled={component.biclique_count <= 1}
                                            title={component.biclique_count <= 1 ? 
                                                "Detailed analysis is only available for complex components" : 
                                                "View component details"
                                            }
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

