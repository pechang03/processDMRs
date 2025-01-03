import React from 'react';
import {
Paper,
Typography,
Table,
TableBody,
TableCell,
TableContainer,
TableHead,
TableRow,
Button,
Box,
} from '@mui/material';

const ComponentSelectionView = ({ 
timepointDetails, 
onComponentSelect,
selectedTimepoint 
}) => {
// Process timepoint component summaries
const componentSummaries = React.useMemo(() => {
    if (!timepointDetails?.components) return [];
    return timepointDetails.components;
}, [timepointDetails]);

return (
    <Box sx={{ mt: 2 }}>
    <Paper elevation={3} sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
        Available Components
        </Typography>
        <TableContainer>
        <Table>
            <TableHead>
            <TableRow>
                <TableCell>Component ID</TableCell>
                <TableCell align="right">Bicliques</TableCell>
                <TableCell align="right">Total Genes</TableCell>
                <TableCell align="right">Total DMRs</TableCell>
                <TableCell align="right">Methylated Regions</TableCell>
                <TableCell>Action</TableCell>
            </TableRow>
            </TableHead>
            <TableBody>
            {componentSummaries.map((component) => (
                <TableRow key={component.component_id}>
                <TableCell>{component.component_id}</TableCell>
                <TableCell align="right">{component.bicliques_count}</TableCell>
                <TableCell align="right">{component.genes_count}</TableCell>
                <TableCell align="right">{component.dmrs_count}</TableCell>
                <TableCell align="right">{component.methylated_regions_count}</TableCell>
                <TableCell>
                    <Button
                    variant="contained"
                    color="primary"
                    onClick={() => onComponentSelect(component.component_id)}
                    >
                    View Details
                    </Button>
                </TableCell>
                </TableRow>
            ))}
            </TableBody>
        </Table>
        </TableContainer>
    </Paper>
    </Box>
);
};

export default ComponentSelectionView;

