import React, { useState } from "react";
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
  Alert,
} from "@mui/material";
import BicliqueGraphView from './BicliqueGraphView.jsx';
import { Tab, Tabs, TabList, TabPanel } from "react-tabs";
import "./BicliqueDetailView.css";

function BicliqueDetailView({ timepointId, componentId }) {
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);
  const [componentDetails, setComponentDetails] = useState(null);

  React.useEffect(() => {
    if (timepointId && componentId) {
      setLoading(true);
      setError(null);
      
      fetch(`http://localhost:5555/api/components/${timepointId}/${componentId}/details`)
        .then(response => {
          if (!response.ok) {
            throw new Error(`Failed to fetch component details: ${response.statusText}`);
          }
          return response.json();
        })
        .then(data => {
          if (data.status === 'success') {
            setComponentDetails(data.data);
          } else {
            throw new Error(data.message || 'Failed to load component details');
          }
        })
        .catch(error => {
          console.error('Error:', error);
          setError(error.message);
        })
        .finally(() => {
          setLoading(false);
        });
    }
  }, [timepointId, componentId]);

  const formatGeneSymbols = (symbols) => {
    if (!symbols) return "";
    if (Array.isArray(symbols)) {
      return symbols.join(", ");
    }
    return String(symbols);
  };

  const formatArray = (arr) => {
    if (!arr) return "";
    if (Array.isArray(arr)) {
      return arr.join(", ");
    }
    return String(arr).replace(/[\[\]']/g, "");
  };

  // Add debug logging for incoming data
  console.log("BicliqueDetailView received:", {
    timepointId,
    timepointDetails,
  });

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        Error loading component details: {error}
      </Alert>
    );
  }

  if (!componentDetails) {
    return <Alert severity="info">No component details available</Alert>;
  }

  const [activeTab, setActiveTab] = useState(0);

  return (
    <Box sx={{ width: "100%", mt: 3 }}>
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          Component Analysis for Timepoint {timepointDetails.name}
        </Typography>
        <Tabs
          onSelect={(index) => setActiveTab(index)}
          selectedIndex={activeTab}
          className="reactTabs"
        >
          <TabList className="reactTabs__tabList">
            <Tab className="reactTabs__tab">Overview</Tab>
            <Tab className="reactTabs__tab">Details</Tab>
          </TabList>

          <TabPanel className="reactTabs__tabPanel">
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
                    <TableRow
                      hover
                      sx={{
                        "&:nth-of-type(odd)": {
                          backgroundColor: "rgba(0, 0, 0, 0.04)",
                        },
                      }}
                    >
                      <TableCell>{componentDetails.component_id}</TableCell>
                      <TableCell>{componentDetails.categories}</TableCell>
                      <TableCell>{componentDetails.graph_type}</TableCell>
                      <TableCell align="right">
                        {componentDetails.total_dmr_count || 0}
                      </TableCell>
                      <TableCell align="right">
                        {componentDetails.total_gene_count || 0}
                      </TableCell>
                      <TableCell>
                        <Typography
                          sx={{
                            maxWidth: 300,
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: "nowrap",
                            fontFamily: "monospace",
                            fontSize: "0.875rem",
                          }}
                          title={componentDetails.all_dmr_ids.join(", ")}
                        >
                          {componentDetails.all_dmr_ids.join(", ")}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography
                          sx={{
                            maxWidth: 400,
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: "nowrap",
                            fontFamily: "monospace",
                            fontSize: "0.875rem",
                            color: "primary.main",
                          }}
                          title={componentDetails.all_gene_ids.join(", ")}
                        >
                          {componentDetails.all_gene_ids.join(", ")}
                        </Typography>
                      </TableCell>
                    </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </TabPanel>
          <TabPanel className="reactTabs__tabPanel">
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
