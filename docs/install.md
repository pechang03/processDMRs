# DMR Analysis System Installation Guide

## Prerequisites

### Required
- Python ≥3.8
- PostgreSQL ≥12.0
- Node.js ≥14.0 (for frontend)
- Conda or Miniconda

### Optional
- Redis (for caching)
- GPU support for LLM features

## Dependencies

### Core Python Packages
- Flask
- NetworkX
- Pandas
- SQLAlchemy
- Plotly
- NumPy
- Poetry (package management)

### Frontend Dependencies
- React
- Material-UI
- Plotly.js
- Axios

## Installation Steps

1. Clone the repository:
```bash
git clone <repository-url>
cd dmr-analysis
```

2. Create and activate conda environment:
```bash
conda create -n dmr-env python=3.8
conda activate dmr-env
```

3. Install backend dependencies:
```bash
poetry install
```

4. Install frontend dependencies:
```bash
cd frontend
npm install
```

## Configuration

1. Create `.env` file in project root:
```env
FLASK_APP=backend/app.py
FLASK_ENV=development
DATABASE_URL=postgresql://user:password@localhost/dmr_db
REDIS_URL=redis://localhost:6379/0  # Optional
```

2. Configure database connection:
```bash
cp config/database.yml.example config/database.yml
# Edit database.yml with your PostgreSQL credentials
```

## Database Setup

1. Create PostgreSQL database:
```bash
createdb dmr_db
```

2. Initialize database schema:
```bash
flask db upgrade
```

## Optional Components

### Test Suite
```bash
# Install test dependencies
poetry install --with test

# Run tests
pytest
```

### LLM Features
```bash
# Install LLM dependencies
poetry install --with llm

# Configure LLM settings in .env
LLM_MODEL=gpt-3
LLM_API_KEY=your-api-key
```

## Basic Usage

1. Start the backend server:
```bash
flask run
```

2. Start the frontend development server:
```bash
cd frontend
npm start
```

3. Access the application:
- Frontend: http://localhost:3000
- API: http://localhost:5000

## Verification

1. Check the installation:
```bash
flask check-install
```

2. Run sample analysis:
```bash
flask run-example
```

## Troubleshooting

- Database connection issues: Check PostgreSQL service status
- Frontend build errors: Clear node_modules and reinstall
- Backend import errors: Verify conda environment activation

