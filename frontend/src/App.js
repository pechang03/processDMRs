import React from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Container from '@mui/material/Container';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

const theme = createTheme({
palette: {
    mode: 'light',
},
});

function App() {
return (
    <ThemeProvider theme={theme}>
    <CssBaseline />
    <Container maxWidth="lg">
        <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
            Welcome to React App
        </Typography>
        </Box>
    </Container>
    </ThemeProvider>
);
}

export default App;

