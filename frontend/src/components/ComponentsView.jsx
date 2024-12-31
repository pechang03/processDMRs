import React, { useState, useEffect } from 'react';
import { Table, Button } from 'react-bootstrap';

function ComponentsView({ selectedTimepoint, onSelectComponent }) {
const [components, setComponents] = useState([]);

useEffect(() => {
    if (selectedTimepoint) {
    fetch(`/api/components?timepoint_id=${selectedTimepoint}`)
        .then(response => response.json())
        .then(data => setComponents(data))
        .catch(error => console.error('Error fetching components:', error));
    }
}, [selectedTimepoint]);

return (
    <div>
    <h3>Components for Timepoint {selectedTimepoint}</h3>
    <Table striped bordered hover>
        <thead>
        <tr>
            <th>Category</th>
            <th>DMR Count</th>
            <th>Gene Count</th>
            <th>Edge Count</th>
            <th>Biclique Count</th>
            <th>Actions</th>
        </tr>
        </thead>
        <tbody>
        {components.map((component) => (
            <tr key={component.component_id}>
            <td>{component.category}</td>
            <td>{component.dmr_count}</td>
            <td>{component.gene_count}</td>
            <td>{component.edge_count}</td>
            <td>{component.biclique_count}</td>
            <td>
                <Button 
                variant="primary"
                onClick={() => onSelectComponent(component.timepoint_id, component.component_id)}
                >
                Select
                </Button>
            </td>
            </tr>
        ))}
        </tbody>
    </Table>
    </div>
);
}

export default ComponentsView;

