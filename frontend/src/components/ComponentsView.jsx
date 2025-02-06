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
    CircularProgress,
    Tabs,
    Tab,
    Alert
} from '@mui/material';
import { API_BASE_URL } from '../config.js';

// Reusable table component
function ComponentTable({ components, onSelectComponent, showCategory }) {
    return (
        <TableContainer>
            <Table>
                <TableHead>
                    <TableRow>
                        <TableCell>Component ID</TableCell>
                        <TableCell align="right">Bicliques</TableCell>
                        <TableCell align="right">Genes</TableCell>
                        <TableCell align="right">DMRs</TableCell>
                        {showCategory && <TableCell>Category</TableCell>}
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
                            {showCategory && <TableCell>{component.biclique_categories}</TableCell>}
                            <TableCell>
                                <Button
                                    variant="contained"
                                    color="primary"
                                    onClick={() => onSelectComponent(component.component_id)}
                                    disabled={showCategory && component.biclique_categories === 'simple'}
                                    title={showCategory && component.biclique_categories === 'simple' ? 
                                        "Detailed analysis is only available for interesting components" : 
                                        "View component details"
                                    }
                                    sx={{
                                        opacity: (showCategory && component.biclique_categories === 'simple') ? 0.6 : 1
                                    }}
                                >
                                    Details
                                </Button>
                            </TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </TableContainer>
    );
}

function ComponentsView({ selectedTimepoint, onSelectComponent }) {
    const [components, setComponents] = useState([]);
    const [timepointName, setTimepointName] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState('split');

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
                            dmr_count: component.dmr_count,
                            graph_type: component.graph_type,
                            biclique_categories: component.biclique_categories
                        })))
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


    const handleTabChange = (event, newValue) => {
        setActiveTab(newValue);
    };

    const filteredComponents = components.filter(component => 
        component.graph_type === activeTab
    );

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
                
                <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
                    <Tabs value={activeTab} onChange={handleTabChange}>
                        <Tab label="Split Components" value="split" />
                        <Tab label="Original Components" value="original" />
                    </Tabs>
                </Box>
                
                <Box sx={{ mt: 2 }}>
                    <ComponentTable 
                        components={filteredComponents}
                        onSelectComponent={onSelectComponent}
                        showCategory={activeTab === 'split'}
                    />
                </Box>
            </Paper>
        </Box>
    );
}

export default ComponentsView;

