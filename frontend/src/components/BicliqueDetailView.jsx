import React, { useState, useMemo } from "react";
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
  Chip,
  Stack,
  Tooltip,
} from "@mui/material";
import BicliqueGraphView from './BicliqueGraphView.jsx';
import { Tab, Tabs, TabList, TabPanel } from "react-tabs";
import "./BicliqueDetailView.css";

function BicliqueDetailView({ timepointId, componentId }) {
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);
  const [componentDetails, setComponentDetails] = useState(null);
  const [geneSymbols, setGeneSymbols] = useState({});
  const [dmrNames, setDmrNames] = useState({});
  const [activeTab, setActiveTab] = useState(0);

  const fetchGeneSymbols = async (geneIds) => {
    try {
      const response = await fetch(`http://localhost:5555/api/genes/symbols`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          gene_ids: geneIds,
          timepoint_id: timepointId 
        })
      });
      if (!response.ok) throw new Error('Failed to fetch gene symbols');
      const data = await response.json();
      setGeneSymbols(data.gene_info);
    } catch (error) {
      console.error('Error fetching gene symbols:', error);
    }
  };

  const fetchDmrNames = async (dmrIds) => {
    try {
      const response = await fetch(`http://localhost:5555/api/dmrs/status`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          dmr_ids: dmrIds,
          timepoint_id: timepointId 
        })
      });
      if (!response.ok) throw new Error('Failed to fetch DMR status');
      const data = await response.json();
      setDmrNames(data.dmr_status);
    } catch (error) {
      console.error('Error fetching DMR names:', error);
    }
  };

  const formatGeneSymbols = (geneIds) => {
    return geneIds.map(id => {
      const info = geneSymbols[id];
      if (!info) return id;
      
      return (
        <Tooltip title={`Degree: ${info.degree}, Bicliques: ${info.biclique_count}`} arrow>
          <span className="node-info">
            {info.symbol || id}
            {info.is_split && <span className="node-badge split">Split</span>}
            {info.is_hub && <span className="node-badge hub">Hub</span>}
          </span>
        </Tooltip>
      );
    });
  };

  const formatDmrNames = (dmrIds) => {
    return dmrIds.map(id => {
      const info = dmrNames[id];
      if (!info) return id;
      
      return (
        <Tooltip title={`Degree: ${info.degree}, Bicliques: ${info.biclique_count}`} arrow>
          <span className="node-info">
            DMR {id}
            {info.is_hub && <span className="node-badge hub">Hub</span>}
          </span>
        </Tooltip>
      );
    });
  };

  const geneStats = useMemo(() => {
    if (!componentDetails?.all_gene_ids) return null;
    
    const stats = {
      total: componentDetails.all_gene_ids.length,
      hubs: 0,
      splits: 0,
      maxDegree: 0,
      minDegree: Infinity,
      totalBicliques: 0
    };
    
    componentDetails.all_gene_ids.forEach(id => {
      const info = geneSymbols[id];
      if (info) {
        if (info.is_hub) stats.hubs++;
        if (info.is_split) stats.splits++;
        stats.maxDegree = Math.max(stats.maxDegree, info.degree || 0);
        stats.minDegree = Math.min(stats.minDegree, info.degree || 0);
        stats.totalBicliques += info.biclique_count || 0;
      }
    });
    
    return stats;
  }, [componentDetails, geneSymbols]);

  const dmrStats = useMemo(() => {
    if (!componentDetails?.all_dmr_ids) return null;
    
    const stats = {
      total: componentDetails.all_dmr_ids.length,
      hubs: 0,
      maxDegree: 0,
      minDegree: Infinity,
      totalBicliques: 0
    };
    
    componentDetails.all_dmr_ids.forEach(id => {
      const info = dmrNames[id];
      if (info) {
        if (info.is_hub) stats.hubs++;
        stats.maxDegree = Math.max(stats.maxDegree, info.degree || 0);
        stats.minDegree = Math.min(stats.minDegree, info.degree || 0);
        stats.totalBicliques += info.biclique_count || 0;
      }
    });
    
    return stats;
  }, [componentDetails, dmrNames]);

  React.useEffect(() => {
    if (timepointId && componentId) {
      setLoading(true);
      setError(null);
      
      console.log(`Fetching details for component ${componentId} from timepoint ${timepointId}`);
      
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
            // Fetch names for IDs
            if (data.data.all_gene_ids.length > 0) {
              fetchGeneSymbols(data.data.all_gene_ids);
            }
            if (data.data.all_dmr_ids.length > 0) {
              fetchDmrNames(data.data.all_dmr_ids);
            }
          } else {
            throw new Error(data.message || 'Failed to load component details');
          }
        })
        .catch(error => {
          console.error('Error:', error);
          if (error.response?.status === 400 && error.response?.data?.biclique_count !== undefined) {
            setError(`This is a simple component with ${error.response.data.biclique_count} biclique(s). Detailed analysis is only available for complex components with multiple bicliques.`);
          } else {
            setError(error.message || 'Failed to load component details');
          }
        })
        .finally(() => {
          setLoading(false);
        });
    }
  }, [timepointId, componentId]);

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

  return (
    <Box sx={{ width: "100%", mt: 3 }}>
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          Component Analysis for Timepoint {componentDetails.timepoint}
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
                        {formatDmrNames(componentDetails.all_dmr_ids)}
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
                        {formatGeneSymbols(componentDetails.all_gene_ids)}
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
      <BicliqueGraphView
        componentId={componentId}
        timepointId={timepointId}
        geneSymbols={geneSymbols}
        dmrNames={dmrNames}
      />
    </Box>
  );
}

export default BicliqueDetailView;
