import React, { useState, useEffect } from "react";
import Plot from "react-plotly.js";
import { Box, Paper, CircularProgress, Alert, Typography } from "@mui/material";
import { API_BASE_URL } from "../config.js";

const BicliqueGraphView = ({ componentId, timepointId, onDMRSelected }) => {
  const [plotData, setPlotData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedDMR, setSelectedDMR] = useState(null);

  const handlePlotClick = (event) => {
    if (event?.points && event.points.length > 0) {
      const clickedText = event.points[0].text || "";
      const match = clickedText.match(/DMR_(\d+)/);
      if (match) {
        const dmrId = parseInt(match[1], 10);
        setSelectedDMR(dmrId);
        // Trigger API call through parent component
        if (onDMRSelected) {
          onDMRSelected(dmrId);
        }
      }
    }
  };

  useEffect(() => {
    const fetchGraphData = async () => {
      if (!componentId || !timepointId) return;

      setLoading(true);
      setError(null);

      try {
        const response = await fetch(
          `${API_BASE_URL}/graph/${timepointId}/${componentId}`,
        );
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setPlotData(data);
      } catch (err) {
        console.error("Error fetching graph data:", err);
        setError("Failed to load graph visualization");
      } finally {
        setLoading(false);
      }
    };

    fetchGraphData();
  }, [componentId, timepointId]);

  if (loading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="400px"
      >
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
    <Paper elevation={3} sx={{ 
        p: 2,
        m: 2,
        width: '100%',
        overflow: 'visible'
    }}>
      <Typography variant="h6" gutterBottom>
        Component {componentId} Visualization
      </Typography>
      <Box sx={{ width: "100%", height: "800px" }}>
        <Plot
          data={plotData?.data || []}
          layout={{
            ...(plotData?.layout || {}),
            autosize: true,
            showlegend: true,
            hovermode: "closest",
            margin: { l: 50, r: 50, t: 50, b: 50 },
            xaxis: {
              showgrid: false,
              zeroline: false,
              showticklabels: false,
              scaleanchor: "y",
              scaleratio: 1,
              range: plotData?.layout?.xaxis?.range || [-3, 3]
            },
            yaxis: {
              showgrid: false,
              zeroline: false,
              showticklabels: false,
              range: plotData?.layout?.yaxis?.range || [-3, 3]
            },
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            width: 1200,
            height: 800,
            margin: { l: 100, r: 100, t: 50, b: 50 }
          }}
          // Node shapes are defined in backend visualization.traces.NODE_SHAPES
          config={{
            displayModeBar: true,
            scrollZoom: true,
            responsive: true,
            modeBarButtonsToAdd: ['select2d', 'lasso2d'],
            modeBarButtonsToRemove: ['autoScale2d']
          }}
          onInitialized={(figure) => {
            console.log('Plotly initialized with figure:', figure);
            console.log('Trace shapes:', figure.data.map(t => t.marker?.symbol));
          }}
          onUpdate={(figure) => {
            console.log('Plotly updated with figure:', figure);
            console.log('Trace shapes:', figure.data.map(t => t.marker?.symbol));
          }}
          style={{ width: "100%", height: "100%" }}
          useResizeHandler={true}
          onClick={(event) => handlePlotClick(event)}
        />
      </Box>
    </Paper>
  );
};

export default BicliqueGraphView;
