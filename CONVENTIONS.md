# Project Conventions and Standards

This document outlines the coding conventions and standards for this project. Following these guidelines ensures consistency, maintainability, and high code quality across the project.

## Database Standards

### Query Patterns

- Use SQLAlchemy ORM for all database operations
- Implement type hints for model classes
- Follow standard naming conventions for tables
- Use consistent field types across related tables

### Pydantic Schemas

- Maintain synchronization between `backend/schemas.py` and SQL views in `backend/app/database/management/sql/views`
- Update both schema definitions when making changes to either
- Test API endpoints after any schema modifications

```python
# Example Pydantic schema in backend/schemas.py
from pydantic import BaseModel
from typing import Optional

class ComponentBase(BaseModel):
    name: str
    type: str
    status: Optional[str]

    class Config:
        orm_mode = True

# Must match corresponding SQL view in backend/app/database/management/sql/views
class ComponentView(ComponentBase):
    id: int
    dmr_id: int
    properties: dict
```

### Schema Maintenance

- Document schema changes in version control
- Validate schema updates against corresponding SQL views
- Include schema validation in CI/CD pipeline
- Run integration tests after schema modifications
- Keep field types consistent between schemas and views

### Database Operations

```python
# Standard model definition
class DMR(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    components = db.relationship('Component', backref='dmr')

# Standard query pattern
def get_dmr(dmr_id: int) -> Optional[DMR]:
    return DMR.query.filter_by(id=dmr_id).first()
```

### Performance Standards

- Cache frequently accessed data
- Use appropriate indexes for search fields
- Implement database connection pooling
- Monitor query performance regularly

## Code Quality Standards

### Avoiding Code Smells

- No duplicate code blocks
- Avoid long methods (keep under 20 lines where possible)
- Maintain single responsibility principle
- Avoid deeply nested conditional statements
- Eliminate dead code and unused variables
- Keep cyclomatic complexity low

### Code Organization

- Use meaningful variable and function names
- Implement proper error handling
- Write unit tests for critical functionality
- Keep classes focused and cohesive
- Document public APIs and complex logic
- Use appropriate design patterns when applicable

## General Coding Practices

### Formatting

- Consistent indentation (4 spaces)
- Maximum line length: 100 characters
- Use clear and consistent naming conventions
- Classes: PascalCase
- Functions/methods: snake_case
- Variables: snake_case
- Constants: UPPER_SNAKE_CASE

### Documentation

- Document all public APIs
- Include docstrings for classes and functions
- Keep comments relevant and up-to-date
- Use type hints where applicable

### Version Control

- Write clear, descriptive commit messages
- Keep commits focused and atomic
- Use feature branches for new development
- Review code before merging

The project follows a structured Flask/React architecture with specific conventions:

### Core Classes

1. **DMRProcessor**

- Processes DMR file inputs using standard parsers
- Creates and maintains database schema
- Implements core data processing methods
- Uses SQLAlchemy for database operations

2. **DMRComponent**

- Encapsulates component-specific logic
- Maintains relationships with parent DMR
- Uses NetworkX for graph operations
- Implements standard graph traversal methods

3. **DMRViewer**

- Handles graph visualization using Plotly
- Maintains consistent layout patterns
- Implements caching for large visualizations
- Uses standard color schemes and styling

### Technology Implementation

**Backend (Flask)**

- Use Flask blueprints for route organization
- Implement RESTful API patterns
- Follow SQLAlchemy ORM practices
- Use standard error handling decorators

**Frontend (React)**

- Implement component-based architecture
- Use React hooks for state management
- Follow container/presentation pattern
- Implement standard API call patterns

**Database Layer**

```sql
-- Standard table structure for DMR data
CREATE TABLE dmr (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    date TEXT,
    status TEXT
);

CREATE TABLE component (
    id INTEGER PRIMARY KEY,
    dmr_id INTEGER REFERENCES dmr(id),
    name TEXT,
    type TEXT,
    status TEXT
);

-- Index for frequent queries
CREATE INDEX idx_component_dmr ON component(dmr_id);
```

### Configuration Standards

- Store all configurations in `.env` file
- Use environment-specific config files
- Keep sensitive data in secure environment variables
- Document all config variables in `.env.example`
- Easy deployment configuration management
  All configuration values should be documented in a `.env.example` file.

### Frontend Configuration

- Runtime configuration is injected via `window.__RUNTIME_CONFIG__` in `index.html`
- Configuration values are exported from `config.js`
- API base URL is configured using `REACT_APP_API_URL`
- Default API endpoint is '/api' if no runtime config is present

Example configuration:

```html
<!-- index.html -->
<script>
  window.__RUNTIME_CONFIG__ = {
    REACT_APP_API_URL: "http://localhost:5555/api",
  };
</script>
```

```javascript
// config.js
const apiBaseUrl = window.__RUNTIME_CONFIG__?.REACT_APP_API_URL || "/api";
export const API_BASE_URL = apiBaseUrl;
```

## ID Conversion Conventions

In this project, we use two different numbering schemes for DMR nodes:

1. **Database DMR IDs (Table Format):**

   - These IDs are designed to match external spreadsheets and other data sources.
   - They must be 1-indexed (or otherwise start from a positive number greater than 0) because these sources do not use 0 as a valid index.
   - Additionally, a timepoint-specific offset (stored in the Timepoint table's `dmr_id_offset` column) is applied so that DMR IDs are unique across timepoints.

2. **Graph Node IDs (NetworkX Graph):**
   - In-memory graph representations (created using NetworkX) require node IDs to start at 0.
   - Many graph algorithms assume 0-indexed nodes, so it is essential to maintain this numbering internally.
   - As a result, raw node IDs in the graphs are 0-indexed and do not include the timepoint offset.

### Conversion Functions

To reconcile the differences between these numbering schemes, we centralize the conversion logic in the module:  
`backend/app/utils/id_mapping.py`.

Key functions include:

- **create_dmr_id:**  
  Converts a raw (0-indexed) node ID into its final table ID by adding the appropriate timepoint offset.  
  For example, if the raw node ID is 79 and the timepoint offset is 10000, then `create_dmr_id(0, timepoint_id)` returns 79.

- **convert_dmr_id:**
  The purpose of this function is to shift the index between the networkx index range which starts at 0 (also the external C code) and the table id for DMR_id which must start at 1 (0 is a reserved index for sqlite)
  A convenience wrapper that applies additional adjustments as needed of +1 shift, when required), typically used when populating the database. Care needs to be taken to not double apply this.

- **reverse_create_dmr_id:**  
  Inverse conversion function used when reading DMR IDs from the database. It converts the table's 1-indexed (and offset) DMR ID back to the 0-indexed graph node ID, so that the two systems stay in sync.

### Summary

- The graph layer uses raw node IDs (starting at 0) to satisfy algorithm requirements.
- The database layer requires DMR IDs which start at 1 (or a higher value according to the timepoint offset) to correctly match spreadsheet or external source numbering.
- All conversions between these formats are handled through backend/app/utils/id_mapping.py. This ensures that each component of the project is aware of and applies the appropriate conversions exactly once.

By maintaining these conventions and using the centralized conversion functions, we keep the numbering consistent across the various parts of the system.

## Project Organization

### Directory Structure

# `USE find backend/app frontend/src backend/tests -type d -not -path "_/\.**pycache**_" -not -path "_/**pycache**_"`

```
project/
├── backend/
│ ├── app/
│ │ ├── visualization/
│ │ ├── database/
│ │ │ └── management/
│ │ │ └── sql/
│ │ │ └── views/
│ │ ├── llm/
│ │ │ └── mission/
│ │ ├── biclique_analysis/
│ │ ├── core/
│ │ ├── config/
│ │ ├── utils/
│ │ └── routes/
│ └── tests/
└── frontend/
├── src/
│ ├── styles/
│ └── components/
```

### Resource Management

- Keep configuration in dedicated config files
- Store sensitive data in environment variables
- Use appropriate logging levels
- Implement proper error handling and logging

### Development Workflow

- Write tests before implementing features (TDD when possible)
- Review code changes through pull requests
- Keep documentation up-to-date
- Regular code quality checks and linting

## Maintenance

- Regular code reviews
- Technical debt management
- Performance monitoring and optimization
- Regular security audits

## Future Implementation: MCP LLM Integration

The following sections outline the planned LLM integration using MCP reference implementation patterns while maintaining compatibility with existing LLMAnalysisView.jsx component.

### Phase 1: Core Architecture

#### Directory Structure

```

backend/app/
├── llm/
│ ├── transport/
│ │ └── stdio/
│ ├── messages/
│ │ └── message_types/
│ ├── chat_handler.py
│ ├── llm_client.py
│ └── system_prompt_generator.py
```

```

```

#### Component Standards

1. **LLM Message Handling**

````python
class LLMMessage(BaseModel):
    message_type: str
    content: dict
    metadata: Optional[dict]

    class Config:
        orm_mode = True


2. **Transport Layer**

- Implement standardized message transport
- Follow reference implementation patterns
- Use consistent error handling
- Maintain connection state management

### Phase 2: Frontend Integration

#### React Component Structure

```javascript
// LLMAnalysisView.jsx conventions
import React, { useState, useEffect } from "react";

const LLMAnalysisView = () => {
  // Standard state management
  const [analysisState, setAnalysisState] = useState({});

  // API interaction patterns
  const handleLLMRequest = async () => {
    // Implementation
  };
};
````

#### Integration Requirements

- Implement WebSocket connections
- Follow standard message formats
- Handle connection states consistently
- Cache analysis results appropriately

### Phase 3: Analysis Implementation

#### Coding Standards

- Use consistent prompt templates
- Implement standard response parsing
- Follow error handling patterns
- Maintain test coverage for all components

#### Testing Requirements

- Unit tests for message handling
- Integration tests for LLM communication
- End-to-end tests for UI integration

# API Conventions

## URL Structure

All API endpoints follow the pattern: `/api/<resource>/<action>`

### Resources

- component
- graph
- gene
- dmr

### URL Patterns

#### Component Routes

- GET `/api/component/:timepoint_id/components/summary` - Get component summary for timepoint
- GET `/api/component/:timepoint_id/components/:component_id/details` - Get detailed component info
- GET `/api/component/:timepoint_id/details` - Get timepoint component details

#### Gene Routes

- POST `/api/component/genes/symbols` - Get gene symbols
- POST `/api/component/genes/annotations` - Get gene annotations

#### DMR Routes

- POST `/api/component/dmrs/status` - Get DMR status

### Response Format

All API responses follow this structure:

```json
{
    "status": "success" | "error",
    "data": <response_data>,
    "message": <error_message>  // Only included for errors
}
```

### Error Handling

HTTP Status Codes:

- 200: Success
- 400: Bad Request
- 404: Not Found
- 500: Server Error

### Query Parameters

Common query parameters:

- timepoint_id: Numeric ID of the timepoint
- component_id: Numeric ID of the component

### Request Bodies

POST requests should include:

- Content-Type: application/json
- Request body in JSON format

### Pagination

When applicable, paginated responses include:

```json
{
    "data": [...],
    "pagination": {
        "page": 1,
        "per_page": 10,
        "total": 100
    }
}
```
