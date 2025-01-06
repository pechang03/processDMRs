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
  Grid,
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
      console.log('Fetching gene symbols for:', geneIds);
      const response = await fetch(`http://localhost:5555/api/genes/symbols`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          gene_ids: geneIds,
          timepoint_id: timepointId,
          component_id: componentId  // Add component_id
        })
      });
      if (!response.ok) throw new Error('Failed to fetch gene symbols');
      const data = await response.json();
      console.log('Received gene data:', data);
      if (data.status === 'success' && data.gene_info) {
        setGeneSymbols(data.gene_info);
      } else {
        throw new Error('Invalid gene data received');
      }
    } catch (error) {
      console.error('Error fetching gene symbols:', error);
    }
  };

  const fetchDmrNames = async (dmrIds) => {
    try {
      console.log('Fetching DMR status for:', dmrIds);
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
      console.log('Received DMR data:', data);
      setDmrNames(data.dmr_status);
    } catch (error) {
      console.error('Error fetching DMR names:', error);
    }
  };

  const formatGeneSymbols = (geneIds) => {
    // Ensure geneIds is an array
    const geneArray = Array.isArray(geneIds) ? geneIds :
                     typeof geneIds === 'string' ? geneIds.split(',').map(id => parseInt(id.trim())) :
                     [];
    
    return geneArray.map(id => {
      const info = geneSymbols[id];
      if (!info) return `Gene ${id}`;
      
      return (
        <Tooltip key={id} title={`Degree: ${info.degree}, Bicliques: ${info.biclique_count}`} arrow>
          <span className="node-info">
            {info.symbol || `Gene ${id}`}
            {info.is_split && <span className="node-badge split">Split</span>}
            {info.is_hub && <span className="node-badge hub">Hub</span>}
          </span>
        </Tooltip>
      );
    });
  };

  const formatDmrNames = (dmrIds) => {
    // Ensure dmrIds is an array
    const dmrArray = Array.isArray(dmrIds) ? dmrIds : 
                    typeof dmrIds === 'string' ? dmrIds.split(',').map(id => parseInt(id.trim())) :
                    [];
    
    return dmrArray.map(id => {
      const info = dmrNames[id];
      if (!info) return `DMR ${id}`;
      
      return (
        <Tooltip key={id} title={`Degree: ${info.degree}, Bicliques: ${info.biclique_count}`} arrow>
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
        if (info.degree !== undefined) {
          stats.maxDegree = Math.max(stats.maxDegree, info.degree);
          stats.minDegree = Math.min(stats.minDegree, info.degree);
        }
        stats.totalBicliques += info.biclique_count || 0;
      }
    });
    
    console.log('Calculated gene stats:', stats); // Debug log
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
        if (info.degree !== undefined) {
          stats.maxDegree = Math.max(stats.maxDegree, info.degree);
          stats.minDegree = Math.min(stats.minDegree, info.degree);
        }
        stats.totalBicliques += info.biclique_count || 0;
      }
    });
    
    console.log('Calculated DMR stats:', stats); // Debug log
    return stats;
  }, [componentDetails, dmrNames]);

  React.useEffect(() => {
    if (timepointId && componentId) {
      setLoading(true);
      setError(null);
      
      console.log(`Fetching details for component ${componentId} from timepoint ${timepointId}`);
      
      fetch(`http://localhost:5555/api/components/${timepointId}/${componentId}/details`)
        .then(response => {
          console.log('Response status:', response.status);
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          console.log('Received component data:', data);
          console.log('Component details:', data.data);
          console.log('Bicliques:', data.data?.bicliques);
          if (data.status === 'success') {
            setComponentDetails(data.data);
            // Fetch gene symbols for all genes in the component
            if (data.data.all_gene_ids && data.data.all_gene_ids.length > 0) {
              fetchGeneSymbols(data.data.all_gene_ids);
            }
            // Fetch DMR status for all DMRs in the component
            if (data.data.all_dmr_ids && data.data.all_dmr_ids.length > 0) {
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
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>Split Genes</Typography>
          <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
            {Object.entries(geneSymbols)
              .filter(([_, info]) => info.is_split)
              .map(([geneId, info]) => (
                <Chip
                  key={geneId}
                  label={`${info.symbol} (${info.biclique_count} bicliques)`}
                  sx={{ m: 0.5 }}
                  color="primary"
                  variant="outlined"
                  title={`Bicliques: ${info.biclique_ids.join(', ')}`}
                />
              ))}
          </Paper>
          <Typography variant="h5" gutterBottom>
            Component Analysis for Timepoint {componentDetails.timepoint}
          </Typography>
          <Stack direction="row" spacing={2} sx={{ mt: 1 }}>
            <Paper variant="outlined" sx={{ p: 2, flex: 1 }}>
              <Typography variant="subtitle2" color="text.secondary">Genes</Typography>
              <Stack direction="row" spacing={1} alignItems="baseline">
                <Typography variant="h6">{geneStats?.total}</Typography>
                <Typography variant="body2" color="text.secondary">
                  ({geneStats?.hubs} hubs, {geneStats?.splits} splits)
                </Typography>
              </Stack>
              <Typography variant="caption" color="text.secondary">
                Degree: {geneStats?.minDegree} - {geneStats?.maxDegree}
              </Typography>
            </Paper>
            <Paper variant="outlined" sx={{ p: 2, flex: 1 }}>
              <Typography variant="subtitle2" color="text.secondary">DMRs</Typography>
              <Stack direction="row" spacing={1} alignItems="baseline">
                <Typography variant="h6">{dmrStats?.total}</Typography>
                <Typography variant="body2" color="text.secondary">
                  ({dmrStats?.hubs} hubs)
                </Typography>
              </Stack>
              <Typography variant="caption" color="text.secondary">
                Degree: {dmrStats?.minDegree} - {dmrStats?.maxDegree}
              </Typography>
            </Paper>
            <Paper variant="outlined" sx={{ p: 2, flex: 1 }}>
              <Typography variant="subtitle2" color="text.secondary">Bicliques</Typography>
              <Typography variant="h6">
                {componentDetails.biclique_count}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {geneStats?.totalBicliques + dmrStats?.totalBicliques} total associations
              </Typography>
            </Paper>
          </Stack>
        </Box>
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
              <Typography variant="h6" gutterBottom>Biclique Details</Typography>
              {console.log('Rendering bicliques:', componentDetails.bicliques)} {/* Debug render */}
              {componentDetails.bicliques && componentDetails.bicliques.map((biclique, index) => (
                <Paper key={biclique.biclique_id} sx={{ p: 2, mb: 2 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    Biclique {index + 1} ({biclique.category})
                  </Typography>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Type</TableCell>
                        <TableCell>Count</TableCell>
                        <TableCell>Members</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      <TableRow>
                        <TableCell>DMRs</TableCell>
                        <TableCell>{biclique.dmr_ids.length}</TableCell>
                        <TableCell>
                          <Box sx={{ 
                            maxWidth: '500px', 
                            overflowX: 'auto',
                            display: 'flex',
                            gap: 1,
                            flexWrap: 'wrap'
                          }}>
                            {formatDmrNames(biclique.dmr_ids)}
                          </Box>
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Genes</TableCell>
                        <TableCell>{biclique.gene_ids.length}</TableCell>
                        <TableCell>
                          <Box sx={{ 
                            maxWidth: '500px', 
                            overflowX: 'auto',
                            display: 'flex',
                            gap: 1,
                            flexWrap: 'wrap'
                          }}>
                            {formatGeneSymbols(biclique.gene_ids).map((gene, idx) => (
                              <Chip
                                key={idx}
                                label={gene}
                                color={geneSymbols[gene.id]?.is_split ? "secondary" : "default"}
                                size="small"
                                sx={{ m: 0.5 }}
                              />
                            ))}
                          </Box>
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </Paper>
              ))}
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
