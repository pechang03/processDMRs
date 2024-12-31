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
// Group bicliques by component_id
const componentSummaries = React.useMemo(() => {
    if (!timepointDetails?.bicliques) return [];
    
    const components = {};
    timepointDetails.bicliques.forEach(biclique => {
    if (!components[biclique.component_id]) {
        components[biclique.component_id] = {
        component_id: biclique.component_id,
        biclique_count: 0,
        total_genes: 0,
        total_dmrs: 0,
        methylated_regions: 0
        };
    }
    
    const comp = components[biclique.component_id];
    comp.biclique_count++;
    comp.total_genes += parseInt(biclique.gene_count || 0);
    comp.total_dmrs += parseInt(biclique.dmr_count || 0);
    if (biclique.graph_type === 'split') {
        comp.methylated_regions++;
    }
    });
    
    return Object.values(components);
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
                <TableCell align="right">{component.biclique_count}</TableCell>
                <TableCell align="right">{component.total_genes}</TableCell>
                <TableCell align="right">{component.total_dmrs}</TableCell>
                <TableCell align="right">{component.methylated_regions}</TableCell>
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

