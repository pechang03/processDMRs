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
IconButton,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import BiotechIcon from "@mui/icons-material/Biotech";
import BicliqueGraphView from "./BicliqueGraphView.jsx";
import { Tab, Tabs, TabList, TabPanel } from "react-tabs";
import "../styles/BicliqueDetailView.css";
import { API_BASE_URL } from "../config.js";

const GeneTable = ({ genes, geneSymbols, geneAnnotations, componentDetails }) => {
  console.log('GeneTable props:', { genes, geneSymbols, geneAnnotations });
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  // Parse the genes string into an array of integers
  const parseGenes = (genesStr) => {
    if (!genesStr) return [];
    if (Array.isArray(genesStr)) return genesStr;
    
    // Add bracket cleaning similar to DMR parsing
    const cleaned = genesStr.replace(/[\[\]]/g, '');
    return cleaned
      .split(',')
      .map((id) => parseInt(id.trim()))
      .filter((id) => !isNaN(id));
  };

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  // Add defensive check for geneSymbols
  if (!geneSymbols) {
    return <Typography>Loading gene information...</Typography>;
  }

  // Parse the genes string before mapping
  const geneArray = parseGenes(genes).map((geneId) => {
    // Add defensive check for each gene ID
    const geneInfo = geneSymbols[geneId] || {
      symbol: `Gene ${geneId}`,
      is_split: false,
      is_hub: false,
      degree: 0,
      biclique_count: 0,
    };

    return {
      id: geneId,
      symbol: geneInfo.symbol || `Gene ${geneId}`,
      type: geneInfo.is_split ? "Split" : geneInfo.is_hub ? "Hub" : "Regular",
      degree: geneInfo.degree || 0,
      biclique_count: geneInfo.biclique_count || 0,
      is_hub: geneInfo.is_hub || false,
      is_split: geneInfo.is_split || false,
    };
  });

  // Add check for empty geneArray
  if (geneArray.length === 0) {
    return <Typography>No genes to display</Typography>;
  }

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
                <TableRow key={`${componentDetails?.component_id}_${gene.id}`}>
                  <TableCell>{gene.id}</TableCell>
                  <TableCell>{gene.symbol}</TableCell>
                  <TableCell>{gene.type}</TableCell>
                  <TableCell align="right">{gene.degree}</TableCell>
                  <TableCell align="right">{gene.biclique_count}</TableCell>
                  <TableCell>
                    <Stack direction="row" spacing={1}>
                      {gene.is_hub && (
                        <Chip size="small" label="Hub" color="primary" />
                      )}
                      {gene.is_split && (
                        <Chip size="small" label="Split" color="secondary" />
                      )}
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

const DMRTable = ({ dmrs, dmrNames, timepointId }) => {
    console.log('DMRTable props:', { dmrs, dmrNames });
    const [page, setPage] = useState(0);
    const [rowsPerPage, setRowsPerPage] = useState(10);

    // Parse the DMRs string into an array of integers
    const parseDMRs = (dmrsStr) => {
        if (!dmrsStr) return [];
        if (Array.isArray(dmrsStr)) return dmrsStr;
        return dmrsStr.replace(/[\[\]]/g, '').split(",").map(id => parseInt(id.trim()));
    };

    const dmrArray = parseDMRs(dmrs);

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
                            .map((dmrId) => {
                                const info = dmrNames[dmrId] || {};
                                return (
                                    <TableRow key={`${timepointId}_${dmrId}`}>
                                        <TableCell>DMR_{dmrId}</TableCell>
                                        <TableCell align="right">{info.degree || 0}</TableCell>
                                        <TableCell align="right">{info.biclique_count || 0}</TableCell>
                                        <TableCell>
                                            <Stack direction="row" spacing={1}>
                                                {info.is_hub && (
                                                    <Chip size="small" label="Hub" color="primary" />
                                                )}
                                            </Stack>
                                        </TableCell>
                                    </TableRow>
                                );
                            })}
                    </TableBody>
                </Table>
            </TableContainer>
            <TablePagination
                rowsPerPageOptions={[5, 10, 25]}
                component="div"
                count={dmrArray.length}
                rowsPerPage={rowsPerPage}
                page={page}
                onPageChange={(event, newPage) => setPage(newPage)}
                onRowsPerPageChange={(event) => {
                    setRowsPerPage(parseInt(event.target.value, 10));
                    setPage(0);
                }}
            />
        </Box>
    );
};

function BicliqueDetailView({ timepointId, componentId }) {
    console.log('Rendering BicliqueDetailView', { componentId, timepointId });
const [loading, setLoading] = React.useState(true);
const [error, setError] = React.useState(null);
const [componentDetails, setComponentDetails] = useState(null);
const [geneSymbols, setGeneSymbols] = useState({});
const [dmrNames, setDmrNames] = useState({});
const [activeTab, setActiveTab] = useState(0);
const [selectedBicliqueForEnrichment, setSelectedBicliqueForEnrichment] = useState(null);
const [enrichmentLoading, setEnrichmentLoading] = useState(false);
const [enrichmentError, setEnrichmentError] = useState(null);
const [enrichmentData, setEnrichmentData] = useState(null);
const [geneAnnotations, setGeneAnnotations] = useState({});
const [selectedDmrForEnrichment, setSelectedDmrForEnrichment] = useState(null);
const [dmrEnrichmentLoading, setDmrEnrichmentLoading] = useState(false);
const [dmrEnrichmentError, setDmrEnrichmentError] = useState(null); 
const [dmrEnrichmentData, setDmrEnrichmentData] = useState(null);
const [dmrDetails, setDmrDetails] = useState(null);

const fetchEnrichmentData = async (bicliqueId) => {
    if (!bicliqueId || !timepointId) return;
    
    setEnrichmentLoading(true);
    setEnrichmentError(null);
    
    try {
        const response = await fetch(`${API_BASE_URL}/enrichment/go-enrichment-biclique/${timepointId}/${bicliqueId}`);
        
        if (!response.ok) {
            throw new Error('Failed to fetch biclique enrichment data');
        }
        
        const data = await response.json();
        setEnrichmentData(data.data);
    } catch (error) {
        setEnrichmentError(error.message);
        console.error('Error fetching enrichment data:', error);
    } finally {
        setEnrichmentLoading(false);
    }
};

const fetchDmrEnrichment = async (dmrId) => {
    console.log('fetchDmrEnrichment called with:', dmrId);
    if (!dmrId || !timepointId) return;
    
    setDmrEnrichmentLoading(true);
    setDmrEnrichmentError(null);
    
    try {
        const response = await fetch(`${API_BASE_URL}/enrichment/go-enrichment-dmr/${timepointId}/${dmrId}`);
        console.log('DMR enrichment response:', response.status);

        if (!response.ok) {
            throw new Error('Failed to fetch DMR enrichment data');
        }

        const data = await response.json();
        console.log('DMR enrichment data received');
        setDmrEnrichmentData(data.data);
        setActiveTab(2); // Switch to Enrichment tab
    } catch (error) {
        console.error('Error in fetchDmrEnrichment:', error);
        setDmrEnrichmentError(error.message);
    } finally {
        setDmrEnrichmentLoading(false);
    }
};

    // Add useEffect to fetch enrichment data when a DMR is selected
    React.useEffect(() => {
        if (selectedDmrForEnrichment) {
            console.log('Fetching enrichment for DMR:', selectedDmrForEnrichment);
            fetchDmrEnrichment(selectedDmrForEnrichment);
        }
    }, [selectedDmrForEnrichment, timepointId]);

    // Add useEffect to fetch enrichment data when a biclique is selected  
    React.useEffect(() => {
        if (selectedBicliqueForEnrichment) {
            fetchEnrichmentData(selectedBicliqueForEnrichment);
        }
    }, [selectedBicliqueForEnrichment, timepointId]);



  const formatGeneSymbols = (geneIds) => {
    // Ensure geneIds is an array
    const geneArray = Array.isArray(geneIds)
      ? geneIds
      : typeof geneIds === "string"
        ? geneIds.split(",").map((id) => parseInt(id.trim()))
        : [];

    return geneArray.map((id) => {
      const info = geneSymbols[id];
      if (!info) return `Gene ${id}`;

      return (
        <Tooltip
          key={id}
          title={`Degree: ${info.degree}, Bicliques: ${info.biclique_count}`}
          arrow
        >
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
    const dmrArray = Array.isArray(dmrIds)
      ? dmrIds
      : typeof dmrIds === "string"
        ? dmrIds.split(",").map((id) => parseInt(id.trim()))
        : [];

    return dmrArray.map((id) => {
      const info = dmrNames[id];
      if (!info) return `DMR ${id}`;

      return (
        <Tooltip
          key={id}
          title={`Degree: ${info.degree}, Bicliques: ${info.biclique_count}`}
          arrow
        >
          <span className="node-info">
            DMR {id}
            {info.is_hub && <span className="node-badge hub">Hub</span>}
          </span>
        </Tooltip>
      );
    });
  };

  const geneStats = useMemo(() => {
    if (!componentDetails?.all_gene_ids || !geneSymbols) {
        console.log("Missing required data for gene stats");
        return null;
    }

    const stats = {
        total: 0,
        hubs: 0,
        splits: 0,
        maxDegree: 0,
        minDegree: Infinity,
        totalBicliques: 0,
    };

    // Convert all_gene_ids to array if it's not already
    const geneIds = Array.isArray(componentDetails.all_gene_ids) 
        ? componentDetails.all_gene_ids 
        : componentDetails.all_gene_ids.split(',').map(id => parseInt(id.trim()));

    stats.total = geneIds.length;
    console.log(`Processing ${stats.total} genes`);

    geneIds.forEach(id => {
        const info = geneSymbols[id];
        if (info) {
            // A gene is split if it appears in multiple bicliques
            if (info.biclique_count > 1) {
                stats.splits++;
                console.log(`Found split gene ${id} (${info.symbol}) in ${info.biclique_count} bicliques`);
            }
            
            if (info.is_hub) {
                stats.hubs++;
                console.log(`Found hub gene ${id} (${info.symbol})`);
            }

            if (info.degree !== undefined) {
                stats.maxDegree = Math.max(stats.maxDegree, info.degree);
                stats.minDegree = Math.min(stats.minDegree, info.degree);
            }

            stats.totalBicliques += info.biclique_count || 0;
        }
    });

    if (stats.minDegree === Infinity) {
        stats.minDegree = 0;
    }

    console.log("Calculated gene stats:", stats);
    return stats;
  }, [componentDetails, geneSymbols]);

  const dmrStats = useMemo(() => {
    if (!componentDetails?.all_dmr_ids || !dmrNames) return null;

    const stats = {
        total: 0,
        hubs: 0,
        maxDegree: 0,
        minDegree: Infinity,
        totalBicliques: 0,
    };

    // Convert all_dmr_ids to array if it's not already
    const dmrIds = Array.isArray(componentDetails.all_dmr_ids) 
        ? componentDetails.all_dmr_ids 
        : componentDetails.all_dmr_ids.split(',').map(id => parseInt(id.trim()));

    stats.total = dmrIds.length;

    dmrIds.forEach(id => {
        const info = dmrNames[id];
        if (info) {
            // Check both node_type and degree for hub status
            if (info.node_type === 'HUB' || info.degree > 5) { // Adjust threshold as needed
                stats.hubs++;
                console.log(`Found hub DMR ${id} with degree ${info.degree}`);
            }

            if (info.degree !== undefined) {
                stats.maxDegree = Math.max(stats.maxDegree, info.degree);
                stats.minDegree = Math.min(stats.minDegree, info.degree);
            }
            stats.totalBicliques += info.biclique_count || 0;
        }
    });

    if (stats.minDegree === Infinity) {
        stats.minDegree = 0;
    }

    console.log("Calculated DMR stats:", stats);
    return stats;
  }, [componentDetails, dmrNames]);

  React.useEffect(() => {
    const abortController = new AbortController();
    
    const fetchAllData = async () => {
        if (!timepointId || !componentId) return;

        setLoading(true);
        setError(null);
        
        try {
            // Fetch all data in parallel with abort signals
            // Fetch all data in parallel with abort signals
            const [
                detailsRes,
                dmrDetailsRes,
                genesSymbolsRes,
                dmrStatusRes,
                edgeStatsRes
            ] = await Promise.all([
                fetch(`${API_BASE_URL}/component/${timepointId}/${componentId}/details`, {
                    signal: abortController.signal
                }),
                fetch(`${API_BASE_URL}/component/${timepointId}/${componentId}/dmr_details`, {
                    signal: abortController.signal
                }),
                fetch(`${API_BASE_URL}/component/genes/symbols`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ timepoint_id: timepointId, component_id: componentId }),
                    signal: abortController.signal
                }),
                fetch(`${API_BASE_URL}/component/dmrs/status`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        dmr_ids: [],
                        timepoint_id: timepointId
                    }),
                    signal: abortController.signal
                }),
                fetch(`${API_BASE_URL}/component/${timepointId}/${componentId}/edge_stats`, {
                    signal: abortController.signal
                }),
            ]);

            // Check for any failed responses
            if (!detailsRes.ok) throw new Error(`Details request failed: ${detailsRes.status}`);
            if (!dmrDetailsRes.ok) throw new Error(`DMR details request failed: ${dmrDetailsRes.status}`);
            if (!genesSymbolsRes.ok) throw new Error(`Genes symbols request failed: ${genesSymbolsRes.status}`);
            if (!dmrStatusRes.ok) throw new Error(`DMR status request failed: ${dmrStatusRes.status}`);
            if (!edgeStatsRes.ok) throw new Error(`Edge stats request failed: ${edgeStatsRes.status}`);

            // Handle responses
            // Parse responses in the exact same order as the fetch calls
            const [
                detailsData,
                dmrDetailsData,
                genesSymbolsData,
                dmrStatusData,
                edgeStatsData
            ] = await Promise.all([
                detailsRes.json(),
                dmrDetailsRes.json(),
                genesSymbolsRes.json(),
                dmrStatusRes.json(),
                edgeStatsRes.json()
            ]);

            // Update state once with all data
            setComponentDetails({
                ...detailsData.data,
                dmr_details: dmrDetailsData.data,
                edge_stats: edgeStatsData.data
            });
            setGeneSymbols(genesSymbolsData.data);
            setDmrNames(dmrStatusData.dmr_status);
        } catch (error) {
            if (error.name === 'AbortError') return;
            console.error("Error fetching data:", error);
            setError(error.message);
        } finally {
            if (!abortController.signal.aborted) {
                setLoading(false);
            }
        }
    };

    fetchAllData();
    
    return () => abortController.abort();
  }, [timepointId, componentId]);

  if (loading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="200px"
      >
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


return (
    <Box sx={{ 
        width: "100%",
        mt: 3,
        maxWidth: "1500px",
        marginX: "auto",
        paddingX: 4
    }}>
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Split Genes
          </Typography>
          <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
            {loading ? (
              <Typography>Loading gene information...</Typography>
            ) : error ? (
              <Typography color="error">{error}</Typography>
            ) : !geneSymbols ? (
              <Typography>No gene information available</Typography>
            ) : (
              <>
                <Typography>Debug: Found {Object.keys(geneSymbols).length} total genes</Typography>
                {Object.entries(geneSymbols).map(([geneId, info]) => {
                  console.log(`Processing gene ${geneId}:`, info);
                  if (info.is_split || info.biclique_count > 1) {
                    return (
                      <Chip
                        key={geneId}
                        label={`${info.symbol || `Gene ${geneId}`} (${info.biclique_count} bicliques)`}
                        sx={{ m: 0.5 }}
                      />
                    );
                  }
                  return null;
                })}
              </>
            )}
          </Paper>
          {/* Add debug section */}
          <Typography variant="h5" gutterBottom>
            Component Analysis for Timepoint {componentDetails.timepoint}
          </Typography>
          <Stack direction="row" spacing={2} sx={{ mt: 1 }}>
            <Paper variant="outlined" sx={{ p: 2, flex: 1 }}>
              <Typography variant="subtitle2" color="text.secondary">
                Genes
              </Typography>
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
              <Typography variant="subtitle2" color="text.secondary">
                DMRs
              </Typography>
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
              <Typography variant="subtitle2" color="text.secondary">
                Bicliques
              </Typography>
              <Typography variant="h6">
                {componentDetails.biclique_count}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {geneStats?.totalBicliques + dmrStats?.totalBicliques} total
                associations
              </Typography>
            </Paper>
          </Stack>
        </Box>
        <Tabs
          onSelect={(index) => setActiveTab(index)}
          selectedIndex={activeTab}
          className="bicliqueDetailTabs"
        >
        <TabList className="bicliqueDetailTabs__tabList">
            <Tab className="bicliqueDetailTabs__tab">Overview</Tab>
            <Tab className="bicliqueDetailTabs__tab">Details</Tab>
            <Tab className="bicliqueDetailTabs__tab">Enrichment</Tab>
        </TabList>

          <TabPanel className="bicliqueDetailTabs__tabPanel" style={{ display: 'block' }}>
            <Box sx={{ maxHeight: "500px", overflow: "auto" }}>
              <Typography variant="h6" gutterBottom>
                Biclique Details
              </Typography>
              {componentDetails.bicliques && componentDetails.bicliques.map((biclique, index) => (
                <Accordion key={biclique.biclique_id}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography>
                      Biclique {index + 1} ({biclique.category}) - {
                        biclique.dmr_ids.split(",").length} DMRs, {
                        biclique.gene_ids.split(",").length} Genes
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="h6" gutterBottom>
                        Genes
                      </Typography>
                      {console.log('Passing to GeneTable:', {
                        genes: biclique.gene_ids,
                        geneSymbols,
                        geneAnnotations
                      })}
                      <GeneTable 
                        genes={biclique.gene_ids}
                        geneSymbols={geneSymbols}
                        geneAnnotations={geneAnnotations}
                        componentDetails={componentDetails}
                      />
                    </Box>
                    <Box>
                      <Typography variant="h6" gutterBottom>
                        DMRs
                      </Typography>
                      {console.log('Passing to DMRTable:', {
                        dmrs: biclique.dmr_ids,
                        dmrNames
                      })}
                      <DMRTable 
                        dmrs={biclique.dmr_ids} 
                        dmrNames={dmrNames}
                        timepointId={timepointId}
                      />
                    </Box>
                  </AccordionDetails>
                </Accordion>
              ))}
            </Box>
          </TabPanel>
          <TabPanel className="bicliqueDetailTabs__tabPanel" style={{ display: 'block' }}>
            <Box sx={{ maxHeight: "500px", overflow: "auto" }}>
              <Typography variant="h6" gutterBottom>
                Detailed Statistics
              </Typography>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Paper elevation={3} sx={{ p: 2 }}>
                    <Typography variant="subtitle1" gutterBottom>
                      Gene Statistics
                    </Typography>
                    <Table size="small">
                      <TableBody>
                        <TableRow>
                          <TableCell>Total Genes</TableCell>
                          <TableCell align="right">{geneStats?.total}</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Hub Genes</TableCell>
                          <TableCell align="right">{geneStats?.hubs}</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Split Genes</TableCell>
                          <TableCell align="right">{geneStats?.splits}</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Degree Range</TableCell>
                          <TableCell align="right">
                            {geneStats?.minDegree} - {geneStats?.maxDegree}
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Total Biclique Participation</TableCell>
                          <TableCell align="right">{geneStats?.totalBicliques}</TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </Paper>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Paper elevation={3} sx={{ p: 2 }}>
                    <Typography variant="subtitle1" gutterBottom>
                      DMR Statistics
                    </Typography>
                    <Table size="small">
                      <TableBody>
                        <TableRow>
                          <TableCell>Total DMRs</TableCell>
                          <TableCell align="right">{dmrStats?.total}</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Hub DMRs</TableCell>
                          <TableCell align="right">{dmrStats?.hubs}</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Degree Range</TableCell>
                          <TableCell align="right">
                            {dmrStats?.minDegree} - {dmrStats?.maxDegree}
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Total Biclique Participation</TableCell>
                          <TableCell align="right">{dmrStats?.totalBicliques}</TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </Paper>
                </Grid>
                
                {/* Add Biclique Summary Section */}
                <Grid item xs={12}>
                  <Paper elevation={3} sx={{ p: 2 }}>
                    <Typography variant="subtitle1" gutterBottom>
                      Edge Classification Statistics
                    </Typography>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Category</TableCell>
                          <TableCell align="right">Component</TableCell>
                          <TableCell align="right">Per Biclique (Average)</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        <TableRow>
                            <TableCell>Accuracy</TableCell>
                            <TableCell align="right">
                                {((componentDetails?.edge_stats?.accuracy ?? 0) * 100).toFixed(1)}%
                            </TableCell>
                            <TableCell align="right">
                                {((componentDetails?.biclique_stats?.average_accuracy ?? 0) * 100).toFixed(1)}%
                            </TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell>Noise Percentage</TableCell>
                            <TableCell align="right">
                                {(componentDetails?.edge_stats?.noise_percentage ?? 0).toFixed(1)}%
                            </TableCell>
                            <TableCell align="right">
                                {(componentDetails?.biclique_stats?.average_noise ?? 0).toFixed(1)}%
                            </TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell>False Positive Rate</TableCell>
                            <TableCell align="right">
                                {((componentDetails?.edge_stats?.false_positive_rate ?? 0) * 100).toFixed(1)}%
                            </TableCell>
                            <TableCell align="right">
                                {((componentDetails?.biclique_stats?.average_fp_rate ?? 0) * 100).toFixed(1)}%
                            </TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell>False Negative Rate</TableCell>
                            <TableCell align="right">
                                {((componentDetails?.edge_stats?.false_negative_rate ?? 0) * 100).toFixed(1)}%
                            </TableCell>
                            <TableCell align="right">
                                {((componentDetails?.biclique_stats?.average_fn_rate ?? 0) * 100).toFixed(1)}%
                            </TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </Paper>

                  <Paper elevation={3} sx={{ p: 2, mt: 2 }}>
                    <Typography variant="subtitle1" gutterBottom>
                      Per-Biclique Edge Statistics
                    </Typography>
                    <TableContainer>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Biclique ID</TableCell>
                            <TableCell align="right">Total Edges</TableCell>
                            <TableCell align="right">Permanent</TableCell>
                            <TableCell align="right">False Positives</TableCell>
                            <TableCell align="right">False Negatives</TableCell>
                            <TableCell align="right">Noise %</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                        {componentDetails?.bicliques?.map((biclique) => {
                        const edge_stats = componentDetails?.edge_stats || {};
                        const permanent = edge_stats.permanent_edges || 0;
                        const falsePos = edge_stats.false_positives || 0;
                        const falseNeg = edge_stats.false_negatives || 0;
                        const total = permanent + falsePos + falseNeg;
                        const noise = total > 0 ? ((falsePos + falseNeg) / total * 100).toFixed(1) : "0.0";
                        return (
                            <TableRow key={biclique.biclique_id}>
                            <TableCell>{biclique.biclique_id}</TableCell>
                            <TableCell align="right">{total}</TableCell>
                            <TableCell align="right">{permanent}</TableCell>
                            <TableCell align="right">{falsePos}</TableCell>
                            <TableCell align="right">{falseNeg}</TableCell>
                            <TableCell align="right">{noise}%</TableCell>
                            </TableRow>
                        );
                        })}\n
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </Paper>

                  <Paper elevation={3} sx={{ p: 2, mt: 2 }}>
                    <Typography variant="subtitle1" gutterBottom>
                      Biclique Summary
                    </Typography>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Biclique ID</TableCell>
                          <TableCell align="right">DMRs</TableCell>
                          <TableCell align="right">Genes</TableCell>
                        <TableCell>Category</TableCell>
                        <TableCell>Enrichment</TableCell>
                        </TableRow>
                    </TableHead>
                      <TableBody>
                        {componentDetails?.bicliques?.map((biclique, index) => (
                          <TableRow key={biclique.biclique_id}>
                            <TableCell>{biclique.biclique_id}</TableCell>
                            <TableCell align="right">
                              {biclique.dmr_ids?.split(',').length || 0}
                            </TableCell>
                            <TableCell align="right">
                              {biclique.gene_ids?.split(',').length || 0}
                            </TableCell>
                            <TableCell>{biclique.category}</TableCell>
                            <TableCell>
                            <Button
                                variant="contained"
                                size="small"
                                disabled={enrichmentLoading}
                                onClick={async () => {
                                    try {
                                        setEnrichmentLoading(true);
                                        setEnrichmentError(null);
                                        const response = await fetch(
                                            `${API_BASE_URL}/enrichment/go-enrichment-biclique/${timepointId}/${biclique.biclique_id}`
                                        );
                                        if (!response.ok) {
                                            throw new Error('Failed to fetch enrichment data');
                                        }
                                        const data = await response.json();
                                        setEnrichmentData(data);
                                        setSelectedBicliqueForEnrichment(biclique.biclique_id);
                                        setActiveTab(2); // Switch to Enrichment tab
                                    } catch (error) {
                                        console.error('Error fetching enrichment:', error);
                                        setEnrichmentError(error.message);
                                    } finally {
                                        setEnrichmentLoading(false);
                                    }
                                }}
                            >
                                {enrichmentLoading ? (
                                    <CircularProgress size={20} sx={{ mr: 1 }} />
                                ) : null}
                                View Enrichment
                            </Button>
                            </TableCell>
                        </TableRow>
                        ))}
                    </TableBody>
                    </Table>
                  </Paper>
                </Grid>
              </Grid>

              {/* Gene Details Table */}
              <Box sx={{ mt: 4 }}>
                <Paper elevation={3} sx={{ p: 2 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    Gene Details
                  </Typography>
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Symbol</TableCell>
                          <TableCell>Type</TableCell>
                          <TableCell align="right">Degree</TableCell>
                          <TableCell>Bicliques</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {Object.entries(geneSymbols).map(([geneId, info]) => {
                          // Add unique key construction with component ID
                          const uniqueKey = `${componentDetails.component_id}_${geneId}`;
                          
                          // Parse biclique IDs string and clean it up
                          const bicliqueIds = info.biclique_ids 
                            ? Array.isArray(info.biclique_ids)
                              ? info.biclique_ids
                              : info.biclique_ids.replace(/[\[\]"\\]/g, '').split(',')
                            : [];
                          
                          return (
                            <TableRow key={uniqueKey}>
                              <TableCell>{info.symbol || `Gene_${geneId}`}</TableCell>
                              <TableCell>
                                {info.is_split ? 'Split' : info.is_hub ? 'Hub' : 'Regular'}
                              </TableCell>
                              <TableCell align="right">{info.degree || 0}</TableCell>
                              <TableCell>
                                {bicliqueIds.length > 0 ? (
                                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                    {bicliqueIds.map((bicliqueId, index) => (
                                      <Chip
                                        key={`${bicliqueId}_${index}`}
                                        label={bicliqueId.trim()}
                                        size="small"
                                        variant="outlined"
                                        sx={{ fontSize: '0.75rem' }}
                                      />
                                    ))}
                                  </Box>
                                ) : (
                                  <Typography variant="body2" color="text.secondary">
                                    None
                                  </Typography>
                                )}
                              </TableCell>
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Paper>
              </Box>

              {/* DMR Details Table */}
              <Paper elevation={3} sx={{ p: 2, mt: 2 }}>
                <Typography variant="subtitle1" gutterBottom>
                  DMR Details
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                    <TableRow>
                        <TableCell>DMR ID</TableCell>
                        <TableCell>Chromosome</TableCell>
                        <TableCell>Start</TableCell>
                        <TableCell>End</TableCell>
                        <TableCell>Methylation Δ</TableCell>
                        <TableCell>P-value</TableCell>
                        <TableCell>Q-value</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell>Degree</TableCell>
                        <TableCell>Bicliques</TableCell>
                        <TableCell padding="none" align="center">En</TableCell>
                    </TableRow>
                    </TableHead>
                    <TableBody>
                      {(dmrDetails || componentDetails?.dmr_details)?.map((dmr) => (
                        <TableRow key={dmr.dmr_id}>
                          <TableCell>DMR_{dmr.dmr_id}</TableCell>
                          <TableCell>{dmr.chromosome}</TableCell>
                          <TableCell>{dmr.start?.toLocaleString()}</TableCell>
                          <TableCell>{dmr.end?.toLocaleString()}</TableCell>
                          <TableCell>{dmr.methylation_diff?.toFixed(2)}</TableCell>
                          <TableCell>{dmr.p_value?.toExponential(2)}</TableCell>
                          <TableCell>{dmr.q_value?.toExponential(2)}</TableCell>
                          <TableCell>
                            <Chip 
                              size="small" 
                              label={dmr.node_type} 
                              color={dmr.node_type === 'hub' ? 'primary' : 'default'}
                            />
                          </TableCell>
                          <TableCell>{dmr.degree}</TableCell>
                          <TableCell>
                            {dmr.biclique_ids?.split(',')?.map((id, index) => (
                              <Chip
                                key={`${id}_${index}`}
                                label={id.trim()}
                                size="small"
                                variant="outlined"
                                sx={{ mr: 0.5, mb: 0.5 }}
                              />
                            ))}
                          </TableCell>
                        <TableCell padding="none" align="center">
                        <IconButton
                            size="small"
                            onClick={() => {
                                console.log('Clicked DMR enrichment for:', dmr.dmr_id);
                                setSelectedDmrForEnrichment(dmr.dmr_id);
                                setActiveTab(2); // Switch to Enrichment tab when clicking the button
                            }}
                            title="View Enrichment"
                        >
                            <BiotechIcon fontSize="small" />
                        </IconButton>
                        </TableCell>
                    </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Paper>
            </Box>
        </TabPanel>
        <TabPanel className="bicliqueDetailTabs__tabPanel" style={{ display: 'block' }}>
        <Box sx={{ maxHeight: "500px", overflow: "auto" }}>
            <Grid container spacing={3}>
            {/* Biclique Enrichment Section */}
            <Grid item xs={12} md={6}>
                <Paper elevation={3} sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                    Biclique Enrichment Analysis
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                    Gene Ontology enrichment analysis for selected biclique genes
                </Typography>
                
                {enrichmentLoading ? (
                    <Box display="flex" justifyContent="center" p={3}>
                    <CircularProgress />
                    </Box>
                ) : enrichmentError ? (
                    <Alert severity="error" sx={{ mb: 2 }}>
                    {enrichmentError}
                    </Alert>
                ) : selectedBicliqueForEnrichment ? (
                    <TableContainer>
                    <Table size="small">
                        <TableHead>
                        <TableRow>
                            <TableCell>Process Name</TableCell>
                            <TableCell>P-value</TableCell>
                            <TableCell>Enrichment Score</TableCell>
                            <TableCell>Source</TableCell>
                        </TableRow>
                        </TableHead>
                        <TableBody>
                        {enrichmentData?.biclique_enrichment?.map((item, index) => (
                            <TableRow key={index}>
                            <TableCell>{item.process}</TableCell>
                            <TableCell>{item.p_value.toExponential(2)}</TableCell>
                            <TableCell>{item.enrichment_score.toFixed(2)}</TableCell>
                            <TableCell>{item.source}</TableCell>
                            </TableRow>
                        ))}
                        </TableBody>
                    </Table>
                    </TableContainer>
                ) : (
                    <Alert severity="info">
                    Select a biclique from the summary table to view enrichment data
                    </Alert>
                )}
                </Paper>
            </Grid>

            {/* DMR Enrichment Section */}
            <Grid item xs={12} md={6}>
                <Paper elevation={3} sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                    DMR Enrichment Analysis
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                    Gene Ontology enrichment analysis for selected DMR regions
                </Typography>
                
                <Alert severity="info">
                    Click "View Enrichment" in the DMR Details table to analyze specific DMR regions
                </Alert>
                {/* DMR enrichment data will be displayed here when implemented */}
                </Paper>
            </Grid>
            </Grid>
        </Box>
        </TabPanel>
        </Tabs>
      </Paper>

      <Paper elevation={3} sx={{ p: 3, mt: 3, position: 'relative', zIndex: 1 }}>
        <BicliqueGraphView
          componentId={componentId}
          timepointId={timepointId}
          geneSymbols={geneSymbols}
          dmrNames={dmrNames}
          onDMRSelected={(dmrId) => {
            console.log('DMR selected:', dmrId);
            setSelectedDmrForEnrichment(dmrId);
            // Fetch edge details
            fetch(`${API_BASE_URL}/edge-details/timepoint/${timepointId}/dmr/${dmrId}`)
              .then(res => res.json())
              .then(data => {
                if (data.edges) {
                  // Update DMR details in state
                  setDmrDetails(data.edges);
                  // Switch to Details tab to show the updated information
                  setActiveTab(1);
                }
              })
              .catch(error => {
                console.error('Error fetching DMR edge details:', error);
              });
          }}
        />
      </Paper>
    </Box>
);
}

export default BicliqueDetailView;
