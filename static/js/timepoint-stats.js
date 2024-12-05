
document.addEventListener('DOMContentLoaded', function() {
    const DEBUG = true;  // Move this here so it's only declared once
    
    function loadTimepointData(timepoint) {
        const tabPane = document.getElementById(timepoint);
        if (!tabPane) {
            console.error(`Tab pane not found for timepoint: ${timepoint}`);
            return;
        }

        const loadingIndicator = tabPane.querySelector('.loading-indicator');
        const statsContainer = tabPane.querySelector('.stats-container');
        const errorContainer = tabPane.querySelector('.error-container');

        // Reset containers
        if (loadingIndicator) loadingIndicator.style.display = 'block';
        if (statsContainer) statsContainer.style.display = 'none';
        if (errorContainer) errorContainer.style.display = 'none';

        fetch(`/stats/timepoint/${timepoint}`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Update the tab content with the new data
                    updateTimepointContent(timepoint, data.data);

                    if (loadingIndicator) loadingIndicator.style.display = 'none';
                    if (statsContainer) statsContainer.style.display = 'block';
                    if (errorContainer) errorContainer.style.display = 'none';
                } else {
                    console.error('Error loading timepoint data:', data.message);
                    if (loadingIndicator) {
                        loadingIndicator.style.display = 'none';
                    }
                    if (errorContainer) {
                        errorContainer.innerHTML = `
                            <div class="alert alert-danger">
                                <h4>Error Loading Data</h4>
                                <p>${data.message}</p>
                                ${DEBUG && data.debug ? `
                                    <div class="debug-info mt-3">
                                        <h5>Debug Information:</h5>
                                        <pre class="error-details">${JSON.stringify(data.debug, null, 2)}</pre>
                                    </div>
                                ` : ''}
                            </div>
                        `;
                        errorContainer.style.display = 'block';
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                if (loadingIndicator) loadingIndicator.style.display = 'none';
                if (errorContainer) {
                    errorContainer.innerHTML = `
                        <div class="alert alert-danger">
                            <h4>Network Error</h4>
                            <p>${error.message}</p>
                            ${DEBUG ? `
                                <div class="debug-info mt-3">
                                    <h5>Debug Information:</h5>
                                    <pre class="error-details">${error.stack}</pre>
                                </div>
                            ` : ''}
                        </div>
                    `;
                    errorContainer.style.display = 'block';
                }
            });
    }

    function updateTimepointContent(timepoint, data) {
        const tabContent = document.querySelector(`#${timepoint}`);
        if (!tabContent) {
            console.error(`Tab content not found for timepoint: ${timepoint}`);
            return;
        }

        if (data.debug) {
            const debugInfo = tabContent.querySelector('.debug-info');
            if (debugInfo) {
                debugInfo.textContent = JSON.stringify(data.debug, null, 2);
                if (DEBUG) {
                    debugInfo.style.display = 'block';
                }
            }
        }

        // Update edge coverage stats if present
        if (data.debug && data.debug.raw_edge_stats) {
            updateEdgeCoverageStats(tabContent, data.debug.raw_edge_stats);
        }

        // Update component statistics
        if (data.stats && data.stats.components) {
            updateComponentStats(tabContent, data.stats);
        }
    }

    function updateEdgeCoverageStats(container, stats) {
        const coverageTable = container.querySelector('.card table');
        if (coverageTable) {
            const rows = coverageTable.querySelectorAll('tbody tr');
            if (rows.length >= 3) {
                // Update single coverage
                rows[0].querySelector('td:last-child').textContent = 
                    `${stats.single_coverage} (${(stats.single_percentage * 100).toFixed(1)}%)`;
            
                // Update multiple coverage
                rows[1].querySelector('td:last-child').textContent = 
                    `${stats.multiple_coverage} (${(stats.multiple_percentage * 100).toFixed(1)}%)`;
            
                // Update uncovered
                rows[2].querySelector('td:last-child').textContent = 
                    `${stats.uncovered} (${(stats.uncovered_percentage * 100).toFixed(1)}%)`;
            }
        }
    }

    // Add these functions before the event listener setup

    function updateComponentStats(tabContent, stats) {
        // Update original graph components table
        const originalCompTable = tabContent.querySelector('#original-components-table');
        if (originalCompTable) {
            const originalStats = stats.components.original;
            updateComponentStatsTable(originalCompTable, originalStats, 'original');
        }

        // Update biclique graph components table
        const bicliqueCompTable = tabContent.querySelector('#biclique-components-table');
        if (bicliqueCompTable) {
            const bicliquesStats = stats.components.biclique;
            updateComponentStatsTable(bicliqueCompTable, bicliquesStats, 'biclique');
        }
    }

    function updateComponentStatsTable(tableElement, stats, type) {
        // Determine which components to update based on type
        const componentTypes = type === 'original'
            ? ['connected', 'biconnected', 'triconnected']
            : ['empty', 'simple', 'interesting', 'complex'];

        componentTypes.forEach(compType => {
            const row = tableElement.querySelector(`.${compType}-row`);
            if (row) {
                if (type === 'original') {
                    // Update original graph row with all columns
                    const cells = {
                        total: row.querySelector('.total-cell'),
                        single_node: row.querySelector('.single-node-cell'),
                        small: row.querySelector('.small-cell'),
                        interesting: row.querySelector('.interesting-cell')
                    };

                    Object.entries(cells).forEach(([key, cell]) => {
                        if (cell) {
                            cell.textContent = stats[compType]?.[key] || 0;
                        }
                    });
                } else {
                    // Update biclique graph row with single count
                    const countCell = row.querySelector('td:last-child');
                    if (countCell) {
                        countCell.textContent = stats.connected?.[compType.replace(' ', '_')] || 0;
                    }
                }
            }
        });
    }

    // Add click handlers to tabs
    document.querySelectorAll('[data-bs-toggle="tab"]').forEach(tab => {
        tab.addEventListener('shown.bs.tab', function (event) {
            const timepoint = event.target.getAttribute('href').substring(1);
            loadTimepointData(timepoint);
        });
    });

    // Load initial tab data
    const activeTab = document.querySelector('.nav-link.active');
    if (activeTab) {
        const timepoint = activeTab.getAttribute('href').substring(1);
        loadTimepointData(timepoint);
    }
});
