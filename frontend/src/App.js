import React from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { Tab, Tabs, TabList, TabPanel } from 'react-tabs';
import 'react-tabs/style/react-tabs.css';
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
import BicliqueDetailView from './components/BicliqueDetailView';
import LLMAnalysisView from './components/LLMAnalysisView';
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
const [selectedTab, setSelectedTab] = React.useState(0);
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
        if (!res.ok) {
            if (res.status === 404) {
                throw new Error('Timepoint not found. The requested timepoint data is unavailable.');
            }
            throw new Error('Failed to fetch timepoint details. Please try again later.');
        }
        return res.json();
    })
    .then(data => {
        console.log("Received biclique data:", data);
        const stats = {
            totalBicliques: data.bicliques ? data.bicliques.length : 0,
            totalDMRs: data.bicliques ? data.bicliques.reduce((sum, b) => sum + parseInt(b.dmr_count || 0), 0) : 0,
            totalGenes: data.bicliques ? data.bicliques.reduce((sum, b) => sum + parseInt(b.gene_count || 0), 0) : 0,
            componentCount: data.bicliques ? new Set(data.bicliques.map(b => b.component_id)).size : 0,
            methylatedRegions: data.bicliques ? data.bicliques.filter(b => b.graph_type === 'split').length : 0,
            significantGenes: data.bicliques ? data.bicliques.filter(b => b.category === 'complex')
                .reduce((sum, b) => sum + parseInt(b.gene_count || 0), 0) : 0
    };
    setTimepointDetails({ bicliques: data.bicliques, stats });
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
        <Typography variant="subtitle1" align="center" gutterBottom>
        Version 1.1.0
        </Typography>
          
        <Tabs
        selectedIndex={selectedTab}
        onSelect={index => setSelectedTab(index)}
        className="react-tabs"
        style={{
            border: 'none',
            borderRadius: theme.shape.borderRadius,
            '& .react-tabs__tab': {
            border: 'none',
            borderBottom: '2px solid transparent',
            '&--selected': {
                borderColor: theme.palette.primary.main,
                color: theme.palette.primary.main
            }
            }
        }}
        >
        <TabList>
            <Tab>Overview</Tab>
            <Tab>Analysis</Tab>
            <Tab disabled={!selectedTimepoint}>Statistics</Tab>
        </TabList>

        <TabPanel>
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
            </Grid>
            </TabPanel>

        <TabPanel>
            <Grid container spacing={3}>
                <Grid item xs={12}>
                    <Paper elevation={3} sx={{ p: 3 }}>
                        <Typography variant="h6" gutterBottom>
                            LLM Analysis Tool
                        </Typography>
                        <LLMAnalysisView 
                            selectedTimepoint={selectedTimepoint}
                            timepointDetails={timepointDetails}
                        />
                    </Paper>
                </Grid>
            </Grid>
        </TabPanel>

        <TabPanel>
            {selectedTimepoint && (
                <Grid item xs={12}>
                    <Box>
                        <Typography variant="h6">
                            Timepoint {timepoints.find(t => t.id === selectedTimepoint)?.name}
                        </Typography>
                        {detailsLoading ? (
                            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                                <CircularProgress />
                            </Box>
                        ) : detailsError ? (
                            <Alert severity="error" sx={{ mt: 2 }}>
                                {detailsError}
                            </Alert>
                        ) : (
                            // Rest of your statistics content
                            // ... (keep the existing content)
                        )}
                    </Box>
                </Grid>
            )}
        </TabPanel>
        </Tabs>
    </Box>
    </Container>
    </ThemeProvider>
  );
}

export default App;

