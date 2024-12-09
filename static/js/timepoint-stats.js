
document.addEventListener('DOMContentLoaded', function() {
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

        // Add retry logic for race conditions
        let retryCount = 0;
        const maxRetries = 3;
        const retryDelay = 1000; // 1 second

        function tryFetch() {
            fetch(`/stats/timepoint/${timepoint}`)
                .then(response => {
                    if (!response.ok) {
                        if (response.status === 404 && retryCount < maxRetries) {
                            retryCount++;
                            console.log(`Retry ${retryCount} for ${timepoint}`);
                            setTimeout(tryFetch, retryDelay);
                            return;
                        }
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.text().then(text => {
                        try {
                            return JSON.parse(text);
                        } catch (e) {
                            console.error('JSON Parse Error:', text.substring(0, 100));
                            throw new Error('Invalid JSON response');
                        }
                    });
                })
                .then(data => {
                    if (data.status === 'success') {
                        try {
                            updateTimepointContent(timepoint, data.data);
                            if (loadingIndicator) loadingIndicator.style.display = 'none';
                            if (statsContainer) statsContainer.style.display = 'block';
                            if (errorContainer) errorContainer.style.display = 'none';
                        } catch (error) {
                            showError(
                                `Error updating content: ${error.message}`,
                                { error: error.stack, data: data.debug }
                            );
                        }
                    } else {
                        showError(data.message, data.debug);
                    }
                })
                .catch(error => {
                    if (retryCount < maxRetries && error.message.includes('Invalid JSON')) {
                        retryCount++;
                        console.log(`Retry ${retryCount} for ${timepoint} due to invalid JSON`);
                        setTimeout(tryFetch, retryDelay);
                    } else {
                        showError(
                            `Network or parsing error: ${error.message}`,
                            { error: error.stack }
                        );
                    }
                });
        }

        tryFetch();
    }

    function showError(message, debug = null) {
        const tabPane = document.querySelector('.tab-pane.active');
        if (!tabPane) return;

        const loadingIndicator = tabPane.querySelector('.loading-indicator');
        const statsContainer = tabPane.querySelector('.stats-container');
        const errorContainer = tabPane.querySelector('.error-container');

        if (loadingIndicator) loadingIndicator.style.display = 'none';
        if (statsContainer) statsContainer.style.display = 'none';
        
        if (errorContainer) {
            errorContainer.innerHTML = `
                <div class="alert alert-danger">
                    <h4>Error</h4>
                    <p>${message}</p>
                    ${window.DEBUG && debug ? `
                        <div class="debug-info mt-3">
                            <h5>Debug Information:</h5>
                            <pre class="error-details">${JSON.stringify(debug, null, 2)}</pre>
                        </div>
                    ` : ''}
                </div>
            `;
            errorContainer.style.display = 'block';
        }
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
                if (window.DEBUG) {
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
