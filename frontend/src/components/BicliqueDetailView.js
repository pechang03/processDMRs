import React, { useState } from 'react';
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
import BicliqueGraphView from './BicliqueGraphView';
import { Tab, Tabs, TabList, TabPanel } from 'react-tabs';
import './BicliqueDetailView.css';

function BicliqueDetailView({ timepointId, timepointDetails }) {
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState(null);
    const [selectedComponent, setSelectedComponent] = useState(null);

    const formatGeneSymbols = (symbols) => {
        if (!symbols) return '';
        if (Array.isArray(symbols)) {
            return symbols.join(', ');
        }
        return String(symbols);
    };

    const formatArray = (arr) => {
        if (!arr) return '';
        if (Array.isArray(arr)) {
            return arr.join(', ');
        }
        return String(arr).replace(/[\[\]']/g, '');
    };

    // Add debug logging for incoming data
    console.log('BicliqueDetailView received:', { timepointId, timepointDetails });
    
    if (!timepointDetails) {
        return <Alert severity="info">No data available for this timepoint</Alert>;
    }
    
    // Add debug logging for incoming data
    console.log('BicliqueDetailView received:', { timepointId, timepointDetails });
    
    if (!timepointDetails) {
        return <Alert severity="info">No data available for this timepoint</Alert>;
    }

    // Ensure components exists and is an array
    const components = Array.isArray(timepointDetails.components) 
        ? timepointDetails.components 
        : [];

    console.log('Components array:', components); // Debug log
    
    if (components.length === 0) {
        return <Alert severity="info">No components found for this timepoint</Alert>;
    }

    const [activeTab, setActiveTab] = useState(0);

    return (
        <Box sx={{ width: '100%', mt: 3 }}>
            <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
                <Typography variant="h5" gutterBottom>
                    Component Analysis for Timepoint {timepointDetails.name}
                </Typography>
                <Tabs onSelect={index => setActiveTab(index)} selectedIndex={activeTab}>
                    <TabList>
                        <Tab>Overview</Tab>
                        <Tab>Details</Tab>
                    </TabList>

                    <TabPanel>
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
                                    <TableCell align="center">Actions</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {components.map((component) => (
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
                                                title={Array.isArray(component.all_dmr_ids) ? 
                                                    component.all_dmr_ids.join(', ') : 
                                                    String(component.all_dmr_ids)}
                                            >
                                                {Array.isArray(component.all_dmr_ids) ? 
                                                    component.all_dmr_ids.join(', ') : 
                                                    String(component.all_dmr_ids)}
                                            </Typography>
                                        </TableCell>
                                        <TableCell>
                                            <Typography
                                                sx={{
                                                    maxWidth: 400,
                                                    overflow: 'hidden',
                                                    textOverflow: 'ellipsis',
                                                    whiteSpace: 'nowrap',
                                                    fontFamily: 'monospace',
                                                    fontSize: '0.875rem',
                                                    color: 'primary.main'
                                                }}
                                                title={Array.isArray(component.gene_symbols) ? 
                                                    component.gene_symbols.join(', ') : 
                                                    String(component.gene_symbols)}
                                            >
                                                {Array.isArray(component.gene_symbols) ? 
                                                    component.gene_symbols.join(', ') : 
                                                    String(component.gene_symbols)}
                                            </Typography>
                                        </TableCell>
                                        <TableCell align="center">
                                            <Button
                                                variant="contained"
                                                color="primary" 
                                                size="small"
                                                onClick={() => setSelectedComponent(component.component_id)}
                                                sx={{
                                                    textTransform: 'none',
                                                    minWidth: '100px'
                                                }}
                                            >
                                                View Graph
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                        </TableContainer>
                    </TabPanel>
                    <TabPanel>
                        {/* Add detailed view here */}
                    </TabPanel>
                </Tabs>
            </Paper>
            {selectedComponent && (
                <BicliqueGraphView 
                    componentId={selectedComponent}
                    timepointId={timepointId}
                />
            )}
        </Box>
    );
}

export default BicliqueDetailView;
