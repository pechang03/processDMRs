import React from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Container from '@mui/material/Container';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import Paper from '@mui/material/Paper';
import Grid from '@mui/material/Grid';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
const [backendStatus, setBackendStatus] = React.useState(null);
const [timepoints, setTimepoints] = React.useState([]);
const [loading, setLoading] = React.useState(true);
const [error, setError] = React.useState(null);
const [selectedTimepoint, setSelectedTimepoint] = React.useState(null);
const [timepointDetails, setTimepointDetails] = React.useState(null);
const [detailsLoading, setDetailsLoading] = React.useState(false);
const [detailsError, setDetailsError] = React.useState(null);

  React.useEffect(() => {
    // Check backend status
    fetch('http://localhost:5555/api/health')
      .then(res => res.json())
      .then(data => setBackendStatus(data.status))
      .catch(err => setBackendStatus('offline'));

    // Fetch timepoints
    fetch('http://localhost:5555/api/timepoints')
      .then(res => {
        if (!res.ok) {
          throw new Error('Failed to fetch timepoints');
        }
        return res.json();
      })
      .then(data => {
        setTimepoints(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

const handleTimepointClick = (timepointId) => {
setSelectedTimepoint(timepointId);
setDetailsLoading(true);
setDetailsError(null);
setTimepointDetails(null);

fetch(`http://localhost:5555/api/timepoint-stats/${timepointId}`)
    .then(res => {
        if (res.status === 404) {
            throw new Error('Timepoint not found. The requested timepoint data is unavailable.');
        }
        if (!res.ok) {
            throw new Error('Failed to fetch timepoint details. Please try again later.');
        }
        return res.json();
    })
    .then(data => {
        const bicliques = data;
        // Calculate statistics from biclique data
        const stats = bicliques.reduce((acc, biclique) => {
            acc.totalBicliques = (acc.totalBicliques || 0) + 1;
            acc.totalDMRs = (acc.totalDMRs || 0) + parseInt(biclique.dmr_count);
            acc.totalGenes = (acc.totalGenes || 0) + parseInt(biclique.gene_count);
            acc.components.add(biclique.component_id);
            acc.categories[biclique.category] = (acc.categories[biclique.category] || 0) + 1;
            acc.graphTypes[biclique.graph_type] = (acc.graphTypes[biclique.graph_type] || 0) + 1;
            return acc;
        }, { components: new Set(), categories: {}, graphTypes: {} });
        
        setTimepointDetails({ bicliques, stats });
        
        setDetailsLoading(false);
    })
    .catch(err => {
        console.error('Error fetching timepoint details:', err);
        setDetailsError(err.message);
        setDetailsLoading(false);
    });
};

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container maxWidth="lg">
        <Box sx={{ my: 4 }}>
          <Typography variant="h3" component="h1" gutterBottom align="center">
            DMR Analysis Dashboard
          </Typography>
          
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Paper elevation={3} sx={{ p: 3, textAlign: 'center' }}>
                <Typography variant="h6" gutterBottom>
                  System Status
                </Typography>
                <Typography color={backendStatus === 'running' ? 'success.main' : 'error.main'}>
                  Backend: {backendStatus || 'Checking...'}
                </Typography>
              </Paper>
            </Grid>

            <Grid item xs={12}>
              <Paper elevation={3} sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Available Timepoints
                </Typography>
                {loading ? (
                  <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                    <CircularProgress />
                  </Box>
                ) : error ? (
                  <Typography color="error">{error}</Typography>
                ) : timepoints.length === 0 ? (
                  <Typography>No timepoints available</Typography>
                ) : (
                  <TableContainer>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>Name</TableCell>
                          <TableCell>Action</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {timepoints.map((timepoint) => (
                          <TableRow key={timepoint.id}>
                            <TableCell>{timepoint.name}</TableCell>
                            <TableCell>
                              <Button
                                variant="contained"
                                color="primary"
                                onClick={() => handleTimepointClick(timepoint.id)}
                              >
                                Select
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}
              </Paper>
            </Grid>

            <Grid item xs={12} md={6}>
              <Paper elevation={3} sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Quick Start
                </Typography>
                <Typography paragraph>
                  Welcome to the DMR Analysis Dashboard. This tool helps you analyze DNA methylation regions and their relationships.
                </Typography>
                <Typography paragraph>
                  Select a timepoint from the table above to begin your analysis.
                </Typography>
              </Paper>
            </Grid>

            <Grid item xs={12} md={6}>
              <Paper elevation={3} sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Recent Activity
                </Typography>
                <Typography>
                  No recent analysis sessions found.
                </Typography>
              </Paper>
            </Grid>
            {selectedTimepoint && (
            <Grid item xs={12}>
                <Paper elevation={3} sx={{ p: 3, mt: 3 }}>
                <Typography variant="h6" gutterBottom>
                    Timepoint Details
                </Typography>
                {detailsLoading ? (
                    <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                    <CircularProgress />
                    </Box>
                ) : detailsError ? (
                    <Alert severity="error" sx={{ width: '100%' }}>{detailsError}</Alert>
                ) : timepointDetails ? (
                    <Box>
                        <Typography variant="h6">Timepoint {timepointDetails?.bicliques?.[0]?.timepoint || ''}</Typography>
                        <Grid container spacing={2} sx={{ mt: 2 }}>
                            <Grid item xs={12} md={4}>
                                <Paper elevation={2} sx={{ p: 2 }}>
                                    <Typography variant="subtitle1">Biclique Statistics</Typography>
                                    <Typography>Total Bicliques: {timepointDetails?.stats?.totalBicliques || 0}</Typography>
                                    <Typography>Active Components: {timepointDetails?.stats?.components?.size || 0}</Typography>
                                    <Typography>Category Distribution:</Typography>
                                    {timepointDetails?.stats?.categories && 
                                        Object.entries(timepointDetails.stats.categories).map(([category, count]) => (
                                            <Typography key={category} sx={{ pl: 2 }}>
                                                {category}: {count} bicliques
                                            </Typography>
                                        ))}
                                </Paper>
                            </Grid>
                            <Grid item xs={12} md={4}>
                                <Paper elevation={2} sx={{ p: 2 }}>
                                    <Typography variant="subtitle1">Gene Statistics</Typography>
                                    <Typography>Total Genes: {timepointDetails?.stats?.totalGenes || 0}</Typography>
                                    <Typography>Average Genes per Biclique: {timepointDetails?.stats?.totalBicliques ? 
                                        Math.round(timepointDetails.stats.totalGenes / timepointDetails.stats.totalBicliques) : 0}
                                    </Typography>
                                </Paper>
                            </Grid>
                            <Grid item xs={12} md={4}>
                                <Paper elevation={2} sx={{ p: 2 }}>
                                    <Typography variant="subtitle1">DMR Statistics</Typography>
                                    <Typography>Total DMRs: {timepointDetails?.stats?.totalDMRs || 0}</Typography>
                                    <Typography>Graph Type Distribution:</Typography>
                                    {timepointDetails?.stats?.graphTypes &&
                                        Object.entries(timepointDetails.stats.graphTypes).map(([type, count]) => (
                                            <Typography key={type} sx={{ pl: 2 }}>
                                                {type}: {count} bicliques
                                            </Typography>
                                        ))}
                                </Paper>
                            </Grid>
                        </Grid>
                    </Box>
                ) : (
                    <Typography>No details available</Typography>
                )}
                </Paper>
            </Grid>
            )}
        </Grid>
        </Box>
      </Container>
    </ThemeProvider>
  );
}

export default App;

