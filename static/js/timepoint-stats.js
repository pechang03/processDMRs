
document.addEventListener('DOMContentLoaded', function() {
    // All the JavaScript from base.html goes here
    const DEBUG = true;  // Move this here so it's only declared once
    
    function loadTimepointData(timepoint) {
        // ... existing loadTimepointData function
    }

    function updateTimepointContent(timepoint, data) {
        // ... existing updateTimepointContent function
    }

    function updateEdgeCoverageStats(container, stats) {
        // ... existing updateEdgeCoverageStats function
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
