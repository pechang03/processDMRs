import React, { useState, useEffect } from 'react';
import Plot from 'react-plotly.js';
import { 
    Box, 
    Paper, 
    CircularProgress, 
    Alert,
    Typography
} from '@mui/material';

const BicliqueGraphView = ({ componentId, timepointId }) => {
    const [plotData, setPlotData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchGraphData = async () => {
            if (!componentId || !timepointId) return;

            setLoading(true);
            setError(null);

            try {
                const response = await fetch(`/api/graph/${timepointId}/${componentId}`);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                setPlotData(data);
            } catch (err) {
                console.error('Error fetching graph data:', err);
                setError('Failed to load graph visualization');
            } finally {
                setLoading(false);
            }
        };

        fetchGraphData();
    }, [componentId, timepointId]);

    if (loading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
                <CircularProgress />
            </Box>
        );
    }

    if (error) {
        return (
            <Box m={2}>
                <Alert severity="error">{error}</Alert>
            </Box>
        );
    }

    if (!plotData) {
        return (
            <Box m={2}>
                <Alert severity="info">No visualization data available</Alert>
            </Box>
        );
    }

    return (
        <Paper elevation={3} sx={{ p: 2, m: 2 }}>
            <Typography variant="h6" gutterBottom>
                Component {componentId} Visualization
            </Typography>
            <Box sx={{ width: '100%', height: '600px' }}>
                <Plot
                    data={plotData.data}
                    layout={{
                        ...plotData.layout,
                        autosize: true,
                        showlegend: true,
                        hovermode: 'closest',
                        margin: { l: 50, r: 50, t: 50, b: 50 },
                        xaxis: { showgrid: false, zeroline: false, showticklabels: false },
                        yaxis: { showgrid: false, zeroline: false, showticklabels: false }
                    }}
                    config={{
                        displayModeBar: true,
                        scrollZoom: true,
                        responsive: true
                    }}
                    style={{ width: '100%', height: '100%' }}
                />
            </Box>
        </Paper>
    );
};

export default BicliqueGraphView;
