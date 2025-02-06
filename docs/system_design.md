                                                                                                                        # DMR Analysis System Design

                                                                                                                        ## Overview
                                                                                                                        The DMR Analysis System is a specialized bioinformatics tool designed to analyze DNA methylation regions (DMRs) and their relationships with genes across multiple timepoints. It combines graph theory algorithms with biological data analysis to identify and visualize important patterns in DNA methylation data.

                                                                                                                        ## System Architecture

                                                                                                                        ### Backend Components
                                                                                                                        - **Flask API Server**: Handles data processing requests and serves analysis results
                                                                                                                        - **Analysis Engine**: Core processing modules for DMR and gene relationship analysis
                                                                                                                        - **Database Layer**: PostgreSQL database with SQLAlchemy ORM
                                                                                                                        - **Cache System**: Optional Redis-based caching for performance optimization

                                                                                                                        ### Analysis Modules
                                                                                                                        1. **Graph Processing Module**
                                                                                                                        - Bipartite graph construction (DMRs-Genes)
                                                                                                                        - Component analysis
                                                                                                                        - Edge classification

                                                                                                                        2. **Biclique Analysis**
                                                                                                                        - Biclique detection algorithms
                                                                                                                        - Classification of bicliques
                                                                                                                        - Graph metrics calculation

                                                                                                                        3. **Graph Statistics**
                                                                                                                        - Coverage analysis
                                                                                                                        - Component statistics
                                                                                                                        - Network metrics

                                                                                                                        ### Processing Pipeline
                                                                                                                        1. Data Ingestion
                                                                                                                        - Excel file processing
                                                                                                                        - Data validation
                                                                                                                        - Gene ID mapping

                                                                                                                        2. Graph Construction
                                                                                                                        - Node creation (DMRs and genes)
                                                                                                                        - Edge creation and validation
                                                                                                                        - Metadata association

                                                                                                                        3. Analysis Execution
                                                                                                                        - Component detection
                                                                                                                        - Biclique identification
                                                                                                                        - Statistical calculations

                                                                                                                        ## Key Components

                                                                                                                        ### Timepoint Processing
                                                                                                                        - **File Management**
                                                                                                                        - DSS1.xlsx (timeseries data)
                                                                                                                        - DSS_PAIRWISE.xlsx (pairwise comparisons)
                                                                                                                        - **Timepoint Naming System**
                                                                                                                        - DSStimeseries (main timeseries)
                                                                                                                        - Pairwise timepoint formats (e.g., P21-P28_TSS)

                                                                                                                        ### Biclique Analysis
                                                                                                                        - **Detection Algorithm**
                                                                                                                        - Complete bipartite subgraph identification
                                                                                                                        - Performance optimizations
                                                                                                                        - **Classification**
                                                                                                                        - Edge categorization (permanent, temporary)
                                                                                                                        - Significance scoring

                                                                                                                        ### Graph Processing
                                                                                                                        - **NetworkX Integration**
                                                                                                                        - Custom graph algorithms
                                                                                                                        - Efficient traversal methods
                                                                                                                        - **Component Analysis**
                                                                                                                        - Connected component detection
                                                                                                                        - Size-based categorization

                                                                                                                        ## Database Schema

                                                                                                                        ### Core Tables
                                                                                                                        - timepoints: Stores timepoint metadata
                                                                                                                        - genes: Gene information and metadata
                                                                                                                        - dmrs: DMR details and statistics
                                                                                                                        - bicliques: Identified biclique data
                                                                                                                        - components: Graph component information

                                                                                                                        ### Supporting Tables
                                                                                                                        - statistics: Analysis results and metrics
                                                                                                                        - metadata: Additional entity metadata
                                                                                                                        - relationships: Entity relationship tracking

                                                                                                                        ## Data Models and Storage

                                                                                                                        ### Primary Models
                                                                                                                        - EdgeInfo: Edge metadata and classification
                                                                                                                        - NodeInfo: Node properties and categorization
                                                                                                                        - BicliqueMeta: Biclique analysis results

                                                                                                                        ### Storage Patterns
                                                                                                                        - PostgreSQL for relational data
                                                                                                                        - Optional Redis caching
                                                                                                                        - File-based storage for raw data

                                                                                                                        ## LLM Integration (Optional)
                                                                                                                        - Analysis interpretation
                                                                                                                        - Pattern recognition
                                                                                                                        - Report generation
                                                                                                                        - Query processing

                                                                                                                        Core Architecture

                                                                                                                        • Modular Design: Explain the benefits of a modular design, such as easier maintenance, scalability, and reusability of
                                                                                                                        components.
                                                                                                                        • Technology Stack: Mention specific versions of libraries (e.g., NetworkX, Plotly, Flask) if they are critical to the
                                                                                                                        system's operation.

                                                                                                                            Key Components
                                                                                                                            --------------

                                                                                                                        1 Data Processing
                                                                                                                        • Excel Input Handling: Describe how the system handles different Excel formats and potential errors.
                                                                                                                        • Bipartite Graph Creation: Explain the process of creating the bipartite graph, including how nodes and edges are
                                                                                                                        added.
                                                                                                                        +Manages gene ID mapping system
                                                                                                                        **Data Organization**
                                                                                                                        ---------------- 1. **File Naming vs Timepoint Naming** - Input Files:
                                                                                                                        _ DSS1.xlsx - Contains the DSStimeseries data
                                                                                                                        _ DSS_PAIRWISE.xlsx - Contains pairwise comparison data - Timepoint Names:
                                                                                                                        _ "DSStimeseries" - Used internally for the main timeseries analysis (from DSS1.xlsx)
                                                                                                                        _ Pairwise timepoints (from DSS_PAIRWISE.xlsx sheets): - "P21-P28_TSS" - "P21-P40_TSS" - "P21-P60_TSS" - "P21-P180_TSS" - "TP28-TP180_TSS" - "TP40-TP180_TSS" - "TP60-TP180_TSS"

                                                                                                                            2. **Data Flow**
                                                                                                                            - Excel Files → Data Loading → Internal Processing → Database
                                                                                                                            - File names are used only for I/O operations
                                                                                                                            - Timepoint names are used for:
                                                                                                                                * Database storage
                                                                                                                                * Results organization
                                                                                                                                * API endpoints
                                                                                                                                * Visualization labels

                                                                                                                            3. **Naming Conventions**
                                                                                                                            - File Names: Original Excel file names (e.g., "DSS1.xlsx")
                                                                                                                            - Internal Names: Standardized timepoint names (e.g., "DSStimeseries")
                                                                                                                            - Database Keys: Uses standardized timepoint names
                                                                                                                            - API Routes: Uses standardized timepoint names
                                                                                                                            - Visualization Labels: Uses timepoint names for labels

                                                                                                                        2 Biclique Analysis
                                                                                                                        • Biclique Identification: Provide a brief overview of the algorithms used to identify bicliques.
                                                                                                                        • Edge Classification: Explain the criteria for classifying edges as permanent, false_positive, or false_negative.
                                                                                                                        3 Dominating Set Analysis
                                                                                                                        • RB-Domination: Implements red-blue domination algorithm for bipartite graphs
                                                                                                                        • Greedy Approach: Uses heap-based greedy selection with utility scoring
                                                                                                                        • Minimization: Includes post-processing to remove redundant dominators
                                                                                                                        • Statistics: Tracks coverage metrics and component-level domination
                                                                                                                        4 Visualization System
                                                                                                                        • Hierarchical Visualization: Describe the hierarchy in more detail, including how components interact.
                                                                                                                        • EdgeInfo Objects: Explain how EdgeInfo objects are used in the visualization process.

                                                                                                                            Data Structures

                                                                                                                        1 EdgeInfo
                                                                                                                        • Edge Metadata: Explain the types of metadata tracked (e.g., sources, classifications).
                                                                                                                        • JSON Serialization: Describe the importance of JSON serialization for data exchange.
                                                                                                                        2 NodeInfo
                                                                                                                        • Node Categorization: Explain how nodes are categorized and why this is important.
                                                                                                                        • Split Genes: Describe the special handling for split genes and its significance.

                                                                                                                            Design Decisions

                                                                                                                        1 Edge Classification
                                                                                                                        • Dictionary-Based Classification: Explain why a dictionary-based system was chosen over other methods.
                                                                                                                        • Backward Compatibility: Describe how the system supports both EdgeInfo objects and raw tuples.
                                                                                                                        2 Layout Strategy
                                                                                                                        • Bipartite Layout: Explain the rationale behind positioning DMRs on the left and genes on the right.
                                                                                                                        • Vertical Spacing: Describe how vertical spacing is calculated and why it is important.
                                                                                                                        3 Component Organization
                                                                                                                        • Modular Trace Creation: Explain the benefits of modular trace creation, such as easier debugging and testing.
                                                                                                                        4 Dominating Set Implementation
                                                                                                                        • Greedy Selection: Chose greedy approach for balance of efficiency and solution quality
                                                                                                                        • Component Integration: Integrated with component analysis for granular insights
                                                                                                                        • Caching Strategy: Cached dominating set results with component statistics

                                                                                                                        Future Considerations

                                                                                                                        1 Performance Optimization
                                                                                                                        • Caching: Discuss potential caching strategies and their benefits.
                                                                                                                        • Batch Processing: Explain how batch processing could improve performance.
                                                                                                                        2 Extensibility
                                                                                                                        • New Edge/Node Types: Provide examples of how new edge/node types could be added.
                                                                                                                        • Visualization System: Discuss potential new features for the visualization system.
                                                                                                                        3 Data Validation
                                                                                                                        • Basic Validation: Explain the current validation methods.
                                                                                                                        • Robust Error Checking: Discuss potential improvements in error checking.

                                                                                                                        # DMR Analysis System Design

                                                                                                                        ## Core Architecture

                                                                                                                        - **Modular design** with clear separation between data processing, analysis, and visualization.
                                                                                                                        - Benefits: Easier maintenance, scalability, and reusability of components.
                                                                                                                        - Uses **NetworkX** for graph operations and **Plotly** for interactive visualizations.
                                                                                                                        - **Flask-based web interface** for result display.

                                                                                                                        ## Key Components

                                                                                                                        1. **Data Processing**

                                                                                                                        - Handles Excel input files containing DMR and gene data.
                                                                                                                        - Creates bipartite graph structure (DMRs to genes).
                                                                                                                        - Manages gene ID mapping system.

                                                                                                                        2. **Biclique Analysis**

                                                                                                                        - Identifies complete bipartite subgraphs.
                                                                                                                        - Classifies bicliques (trivial, small, interesting).
                                                                                                                        - Tracks edge classifications and sources.

                                                                                                                        3. **Visualization System**

                                                                                                                        - Hierarchical visualization components:
                                                                                                                        - Core plotting (create_biclique_visualization)
                                                                                                                        - Trace creation (nodes, edges, biclique boxes)
                                                                                                                        - Layout management
                                                                                                                        - Uses EdgeInfo objects to track edge metadata.
                                                                                                                        - Supports multiple input formats for flexibility.

                                                                                                                        ## Data Structures

                                                                                                                        1. **EdgeInfo**

                                                                                                                        - Encapsulates edge data and metadata.
                                                                                                                        - Tracks edge sources and classifications.
                                                                                                                        - Supports JSON serialization.

                                                                                                                        2. **NodeInfo**

                                                                                                                        - Manages node categorization (DMR vs gene).
                                                                                                                        - Tracks split genes and node degrees.
                                                                                                                        - Provides type checking methods.

                                                                                                                        ## Design Decisions

                                                                                                                        1. **Edge Classification**

                                                                                                                        - Uses dictionary-based classification system.
                                                                                                                        - Categories: permanent, false_positive, false_negative.
                                                                                                                        - Supports both EdgeInfo objects and raw tuples for backward compatibility.

                                                                                                                        2. **Layout Strategy**

                                                                                                                        - Bipartite layout with DMRs on left, genes on right.
                                                                                                                        - Special handling for split genes (positioned slightly offset).
                                                                                                                        - Vertical spacing based on biclique sizes.

                                                                                                                        3. **Component Organization**

                                                                                                                        - Separate modules for different visualization aspects.
                                                                                                                        - Clear hierarchy of functionality.
                                                                                                                        - Modular trace creation for maintainability.

                                                                                                                        ## Future Considerations

                                                                                                                        1. **Performance Optimization**

                                                                                                                        - May need caching for large graphs.
                                                                                                                        - Consider batch processing for edge traces.

                                                                                                                        2. **Extensibility**

                                                                                                                        - Design supports adding new edge/node types.
                                                                                                                        - Visualization system can be extended for new features.

                                                                                                                        3. **Data Validation**

                                                                                                                        - Currently implements basic validation.
                                                                                                                        - May need more robust error checking.
                                                                                                                        templates/  
                                                                                                                        ├── layouts/
                                                                                                                        │ └── base.html  
                                                                                                                        ├── components/  
                                                                                                                        │ ├── overall_stats.html # Overall statistics  
                                                                                                                        │ ├── graph_components.html # Graph component statistics  
                                                                                                                        │ └── stats/  
                                                                                                                        │ ├── timepoint_tabs.html # Tab navigation  
                                                                                                                        │ ├── timepoint_tab.html # Individual timepoint content  
                                                                                                                        │ ├── coverage.html # Coverage statistics  
                                                                                                                        │ ├── edge_coverage.html # Edge coverage statistics  
                                                                                                                        │ └── biclique_graph.html # Biclique graph statistics  
                                                                                                                        └── statistics.html # Main template  


                                                                                                                        # System Design Overview

                                                                                                                        ## Application Architecture

                                                                                                                        ### Frontend
                                                                                                                        - Modern Single Page Application (SPA) built with React
                                                                                                                        - Material-UI framework for consistent UI components
                                                                                                                        - Webpack configuration for:
                                                                                                                        - Development server (port 3000)
                                                                                                                        - Hot module replacement
                                                                                                                        - Production builds
                                                                                                                        - Asset optimization
                                                                                                                        - Development setup with npm scripts
                                                                                                                        - Component-based architecture

                                                                                                                        ### Backend
                                                                                                                        - Flask API server running on port 5000
                                                                                                                        - RESTful endpoints for:
                                                                                                                        - Data processing
                                                                                                                        - Analysis operations
                                                                                                                        - Visualization data
                                                                                                                        - CORS configuration for frontend communication
                                                                                                                        - Python-based business logic
                                                                                                                        - JSON response format

                                                                                                                        ### Frontend-Backend Communication
                                                                                                                        - HTTP/REST API calls from React to Flask
                                                                                                                        - Axios for API requests
                                                                                                                        - Backend endpoints accessible at http://localhost:5000/api/
                                                                                                                        - CORS headers to allow frontend access
                                                                                                                        - JSON data exchange format

                                                                                                                        ### Development Environment
                                                                                                                        1. Frontend Setup:
                                                                                                                        ```bash
                                                                                                                        cd frontend
                                                                                                                        npm install
                                                                                                                        npm start  # Runs on port 3000
                                                                                                                        ```

                                                                                                                        2. Backend Setup:
                                                                                                                        ```bash
                                                                                                                        cd backend
                                                                                                                        flask run  # Runs on port 5000
                                                                                                                        ```

                                                                                                                        3. Development Tools:
                                                                                                                        - React Developer Tools
                                                                                                                        - Flask Debug Mode
                                                                                                                        - Hot reloading for both frontend and backend
                                                                                                                        - Webpack Dev Server proxy configuration
                                                                                                                        ### Database Layer

                                                                                                                        - PostgreSQL for data storage
                                                                                                                        - SQLAlchemy ORM for database interactions

                                                                                                                        ### Data Processing

                                                                                                                        - Pandas for data manipulation
                                                                                                                        - NetworkX for graph operations
                                                                                                                        - Custom modules for biclique analysis, component analysis, and statistics calculation

                                                                                                                        ### Visualization

                                                                                                                        - Plotly for interactive visualizations
                                                                                                                        - Custom visualization modules for specific graph layouts

                                                                                                                        ## Database Schema

                                                                                                                        ### Core Entity Tables

                                                                                                                        **timepoints**

                                                                                                                        - id (PK)
                                                                                                                        - name
                                                                                                                        - description

                                                                                                                        **genes**

                                                                                                                        - id (PK)
                                                                                                                        - symbol
                                                                                                                        - description

                                                                                                                        **dmrs**

                                                                                                                        - id (PK)
                                                                                                                        - name
                                                                                                                        - area_stat
                                                                                                                        - description

                                                                                                                        ### Bicliques Table

                                                                                                                        **bicliques**

                                                                                                                        - id (PK)
                                                                                                                        - timepoint_id (FK)
                                                                                                                        - component_id (FK)
                                                                                                                        - dmr_ids (ARRAY)
                                                                                                                        - gene_ids (ARRAY)

                                                                                                                        ### Components Table

                                                                                                                        **components**

                                                                                                                        - id (PK)
                                                                                                                        - timepoint_id (FK)
                                                                                                                        - category
                                                                                                                        - size
                                                                                                                        - dmr_count
                                                                                                                        - gene_count
                                                                                                                        - edge_count
                                                                                                                        - density

                                                                                                                        **component_bicliques** (Junction Table)

                                                                                                                        - component_id (FK)
                                                                                                                        - biclique_id (FK)

                                                                                                                        ### Statistics Tables

                                                                                                                        **statistics**

                                                                                                                        - id (PK)
                                                                                                                        - category
                                                                                                                        - key
                                                                                                                        - value

                                                                                                                        ### Supporting Tables

                                                                                                                        **metadata**

                                                                                                                        - id (PK)
                                                                                                                        - entity_type (e.g., 'gene', 'dmr')
                                                                                                                        - entity_id (FK)
                                                                                                                        - key
                                                                                                                        - value

                                                                                                                        **relationships**

                                                                                                                        - id (PK)
                                                                                                                        - source_entity_type
                                                                                                                        - source_entity_id (FK)
                                                                                                                        - target_entity_type
                                                                                                                        - target_entity_id (FK)
                                                                                                                        - relationship_type

                                                                                                                        ## Indexing

                                                                                                                        - Index on `timepoints.name` for quick lookup
                                                                                                                        - Index on `genes.symbol` for fast gene searches
                                                                                                                        - Index on `bicliques.timepoint_id` and `bicliques.component_id` for performance in queries involving timepoints and components
                                                                                                                        - Composite index on `component_bicliques(component_id, biclique_id)` for efficient joins

                                                                                                                        ## Example Queries

                                                                                                                        ### Find all bicliques for a specific timepoint:

                                                                                                                        ```sql
                                                                                                                        SELECT * FROM bicliques WHERE timepoint_id = (SELECT id FROM timepoints WHERE name = 'DSS1');
                                                                                                                        ```

                                                                                                                        ### Get statistics for a specific category:

                                                                                                                        ```sql
                                                                                                                        SELECT key, value FROM statistics WHERE category = 'coverage';
                                                                                                                        ```

                                                                                                                        ### Retrieve genes in a specific biclique:

                                                                                                                        ```sql
                                                                                                                        SELECT g.* FROM genes g
                                                                                                                        JOIN bicliques b ON b.gene_ids @> ARRAY[g.id]
                                                                                                                        WHERE b.id = 1;
                                                                                                                        ```

                                                                                                                        ## Schema Design Decisions

                                                                                                                        - **Normalization**: Core entities like genes and DMRs are normalized to avoid data redundancy.
                                                                                                                        - **Array Columns**: Used in `bicliques` table to store multiple DMRs and genes, allowing for efficient querying of biclique members.
                                                                                                                        - **Junction Table**: `component_bicliques` to manage many-to-many relationship between components and bicliques.
                                                                                                                        - **Key-Value Design**: For statistics, allowing for flexible storage of various metrics without altering the schema for each new statistic.
                                                                                                                        - **Metadata Table**: To store additional information about entities without bloating the main tables.
                                                                                                                        - **Relationships Table**: To capture complex relationships between different entities, allowing for future expansion of relationship types.

                                                                                                                        This design aims to balance between query performance, data integrity, and flexibility for future enhancements in the analysis pipeline.
