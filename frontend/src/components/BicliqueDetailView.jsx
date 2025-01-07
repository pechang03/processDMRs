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
  TablePagination,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from "@mui/material";
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import BicliqueGraphView from './BicliqueGraphView.jsx';
import { Tab, Tabs, TabList, TabPanel } from "react-tabs";
import "./BicliqueDetailView.css";

const GeneTable = ({ genes, geneSymbols }) => {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const geneArray = genes.map(geneId => ({
    id: geneId,
    ...geneSymbols[geneId]
  }));

  return (
    <Box>
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Gene ID</TableCell>
              <TableCell>Symbol</TableCell>
              <TableCell>Type</TableCell>
              <TableCell align="right">Degree</TableCell>
              <TableCell align="right">Biclique Count</TableCell>
              <TableCell>Properties</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {geneArray
              .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
              .map((gene) => (
                <TableRow key={gene.id}>
                  <TableCell>{gene.id}</TableCell>
                  <TableCell>{gene.symbol}</TableCell>
                  <TableCell>
                    {gene.is_split ? 'Split' : gene.is_hub ? 'Hub' : 'Regular'}
                  </TableCell>
                  <TableCell align="right">{gene.degree}</TableCell>
                  <TableCell align="right">{gene.biclique_count}</TableCell>
                  <TableCell>
                    <Stack direction="row" spacing={1}>
                      {gene.is_hub && <Chip size="small" label="Hub" color="primary" />}
                      {gene.is_split && <Chip size="small" label="Split" color="secondary" />}
                    </Stack>
                  </TableCell>
                </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      <TablePagination
        rowsPerPageOptions={[5, 10, 25]}
        component="div"
        count={geneArray.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
      />
    </Box>
  );
};

const DMRTable = ({ dmrs, dmrNames }) => {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const dmrArray = dmrs.map(dmrId => ({
    id: dmrId,
    ...dmrNames[dmrId]
  }));

  return (
    <Box>
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>DMR ID</TableCell>
              <TableCell align="right">Degree</TableCell>
              <TableCell align="right">Biclique Count</TableCell>
              <TableCell>Properties</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {dmrArray
              .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
              .map((dmr) => (
                <TableRow key={dmr.id}>
                  <TableCell>DMR_{dmr.id}</TableCell>
                  <TableCell align="right">{dmr.degree}</TableCell>
                  <TableCell align="right">{dmr.biclique_count}</TableCell>
                  <TableCell>
                    <Stack direction="row" spacing={1}>
                      {dmr.is_hub && <Chip size="small" label="Hub" color="primary" />}
                    </Stack>
                  </TableCell>
                </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      <TablePagination
        rowsPerPageOptions={[5, 10, 25]}
        component="div"
        count={dmrArray.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
      />
    </Box>
  );
};

function BicliqueDetailView({ timepointId, componentId }) {
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);
  const [componentDetails, setComponentDetails] = useState(null);
  const [geneSymbols, setGeneSymbols] = useState({});
  const [dmrNames, setDmrNames] = useState({});
  const [activeTab, setActiveTab] = useState(0);

  const fetchGeneSymbols = async (geneIds) => {
    try {
      console.log('Fetching gene symbols for component:', componentId);
      const response = await fetch(`http://localhost:5555/api/genes/symbols`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          timepoint_id: timepointId,
          component_id: componentId
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
              {componentDetails.bicliques && componentDetails.bicliques.map((biclique, index) => (
                <Accordion key={biclique.biclique_id}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography>
                      Biclique {index + 1} ({biclique.category}) - 
                      {biclique.dmr_ids.length} DMRs, {biclique.gene_ids.length} Genes
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="h6" gutterBottom>Genes</Typography>
                      <GeneTable 
                        genes={biclique.gene_ids} 
                        geneSymbols={geneSymbols}
                      />
                    </Box>
                    <Box>
                      <Typography variant="h6" gutterBottom>DMRs</Typography>
                      <DMRTable 
                        dmrs={biclique.dmr_ids} 
                        dmrNames={dmrNames}
                      />
                    </Box>
                  </AccordionDetails>
                </Accordion>
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
