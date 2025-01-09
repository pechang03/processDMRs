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
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import BicliqueGraphView from "./BicliqueGraphView.jsx";
import { Tab, Tabs, TabList, TabPanel } from "react-tabs";
import "../styles/BicliqueDetailView.css";
import { API_BASE_URL } from "../config.js";

const GeneTable = ({ genes, geneSymbols, geneAnnotations }) => {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  // Parse the genes string into an array of integers
  const parseGenes = (genesStr) => {
    if (!genesStr) return [];
    if (Array.isArray(genesStr)) return genesStr;
    return genesStr
      .split(",")
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
                <TableRow key={gene.id}>
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

const DMRTable = ({ dmrs, dmrNames }) => {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  // Parse the DMRs string into an array of integers
  const parseDMRs = (dmrsStr) => {
    if (!dmrsStr) return [];
    if (Array.isArray(dmrsStr)) return dmrsStr;
    return dmrsStr.split(",").map((id) => parseInt(id.trim()));
  };

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  // Parse the DMRs string before mapping
  const dmrArray = parseDMRs(dmrs).map((dmrId) => ({
    id: dmrId,
    ...dmrNames[dmrId],
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
                      {dmr.is_hub && (
                        <Chip size="small" label="Hub" color="primary" />
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

  const [geneAnnotations, setGeneAnnotations] = useState({});

  // For basic symbol lookup
  const fetchGeneSymbols = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/component/genes/symbols`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          timepoint_id: timepointId,
          component_id: componentId,
        }),
      });
      if (!response.ok) throw new Error("Failed to fetch gene symbols");
      const data = await response.json();
      if (data.status === "success" && data.data) {
        setGeneSymbols(data.data);
      } else {
        throw new Error("Invalid gene data received");
      }
    } catch (error) {
      console.error("Error fetching gene symbols:", error);
    }
  };

  // For detailed gene information
  const fetchGeneAnnotations = async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/component/genes/annotations`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            timepoint_id: timepointId,
            component_id: componentId,
          }),
        },
      );
      if (!response.ok) throw new Error("Failed to fetch gene annotations");
      const data = await response.json();
      if (data.status === "success" && data.gene_info) {
        setGeneAnnotations(data.gene_info);
      }
    } catch (error) {
      console.error("Error fetching gene annotations:", error);
    }
  };

  const fetchDmrNames = async (dmrIds) => {
    try {
      console.log("Fetching DMR status for:", dmrIds);
      const response = await fetch(`${API_BASE_URL}/component/dmrs/status`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          dmr_ids: dmrIds,
          timepoint_id: timepointId,
        }),
      });
      if (!response.ok) throw new Error("Failed to fetch DMR status");
      const data = await response.json();
      console.log("Received DMR data:", data);
      setDmrNames(data.dmr_status);
    } catch (error) {
      console.error("Error fetching DMR names:", error);
    }
  };

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
    if (!componentDetails?.all_gene_ids || !geneSymbols) return null;

    const stats = {
      total: componentDetails.all_gene_ids.length,
      hubs: 0,
      splits: 0,
      maxDegree: 0,
      minDegree: Infinity,
      totalBicliques: 0,
    };

    componentDetails.all_gene_ids.forEach((id) => {
      const info = geneSymbols[id];
      if (info) {
        // Add null check here
        if (info.is_hub) stats.hubs++;
        if (info.is_split) stats.splits++;
        if (info.degree !== undefined) {
          stats.maxDegree = Math.max(stats.maxDegree, info.degree);
          stats.minDegree = Math.min(stats.minDegree, info.degree);
        }
        stats.totalBicliques += info.biclique_count || 0;
      }
    });

    // If no valid degrees were found, reset minDegree
    if (stats.minDegree === Infinity) {
      stats.minDegree = 0;
    }

    console.log("Calculated gene stats:", stats); // Debug log
    return stats;
  }, [componentDetails, geneSymbols]);

  const dmrStats = useMemo(() => {
    if (!componentDetails?.all_dmr_ids) return null;

    const stats = {
      total: componentDetails.all_dmr_ids.length,
      hubs: 0,
      maxDegree: 0,
      minDegree: Infinity,
      totalBicliques: 0,
    };

    componentDetails.all_dmr_ids.forEach((id) => {
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

    console.log("Calculated DMR stats:", stats); // Debug log
    return stats;
  }, [componentDetails, dmrNames]);

  React.useEffect(() => {
    if (timepointId && componentId) {
      setLoading(true);
      setError(null);

      // Fetch component details
      fetch(`${API_BASE_URL}/component/${timepointId}/${componentId}/details`)
        .then((response) => {
          if (!response.ok) throw new Error("Failed to load component details");
          return response.json();
        })
        .then((data) => {
          if (data.status === "success") {
            setComponentDetails(data.data);
            // Fetch gene symbols and annotations
            return Promise.all([
              fetch(`${API_BASE_URL}/component/genes/symbols`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  timepoint_id: timepointId,
                  component_id: componentId,
                }),
              }),
              fetch(`${API_BASE_URL}/component/genes/annotations`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  timepoint_id: timepointId,
                  component_id: componentId,
                }),
              }),
            ]);
          }
        })
        .then(([symbolsResponse, annotationsResponse]) =>
          Promise.all([symbolsResponse.json(), annotationsResponse.json()]),
        )
        .then(([symbolsData, annotationsData]) => {
          if (symbolsData.status === "success") {
            setGeneSymbols(symbolsData.gene_info);
          }
          if (annotationsData.status === "success") {
            setGeneAnnotations(annotationsData.gene_info);
          }
        })
        .catch((error) => {
          console.error("Error:", error);
          setError(error.message);
        })
        .finally(() => {
          setLoading(false);
        });
    }
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

  if (!componentDetails) {
    return <Alert severity="info">No component details available</Alert>;
  }

  return (
    <Box sx={{ width: "100%", mt: 3 }}>
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Split Genes
          </Typography>
          <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
            {geneSymbols &&
              Object.entries(geneSymbols || {})
                .filter(([_, info]) => info?.is_split)
                .map(([geneId, info]) => (
                  <Chip
                    key={geneId}
                    label={`${info.symbol || `Gene ${geneId}`} (${info.biclique_count || 0} bicliques)`}
                    sx={{ m: 0.5 }}
                    color="primary"
                    variant="outlined"
                    title={`Bicliques: ${info.biclique_ids ? info.biclique_ids.join(", ") : ""}`}
                  />
                ))}
          </Paper>
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
          </TabList>

          <TabPanel className="bicliqueDetailTabs__tabPanel">
            <Box sx={{ maxHeight: "500px", overflow: "auto" }}>
              <Typography variant="h6" gutterBottom>
                Biclique Details
              </Typography>
              {componentDetails.bicliques &&
                componentDetails.bicliques.map((biclique, index) => (
                  <Accordion key={biclique.biclique_id}>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Typography>
                        Biclique {index + 1} ({biclique.category}) -
                        {biclique.dmr_ids.split(",").length} DMRs,{" "}
                        {biclique.gene_ids.split(",").length} Genes
                      </Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Box sx={{ mb: 3 }}>
                        <Typography variant="h6" gutterBottom>
                          Genes
                        </Typography>
                        <GeneTable
                          genes={biclique.gene_ids}
                          geneSymbols={geneSymbols}
                          geneAnnotations={geneAnnotations}
                        />
                      </Box>
                      <Box>
                        <Typography variant="h6" gutterBottom>
                          DMRs
                        </Typography>
                        <DMRTable dmrs={biclique.dmr_ids} dmrNames={dmrNames} />
                      </Box>
                    </AccordionDetails>
                  </Accordion>
                ))}
            </Box>
          </TabPanel>
          <TabPanel className="bicliqueDetailTabs__tabPanel">
            {/* Add detailed view here */}
          </TabPanel>
        </Tabs>
      </Paper>

      <Paper elevation={3} sx={{ p: 3, mt: 3 }}>
        <BicliqueGraphView
          componentId={componentId}
          timepointId={timepointId}
          geneSymbols={geneSymbols}
          dmrNames={dmrNames}
        />
      </Paper>
    </Box>
  );
}

export default BicliqueDetailView;
