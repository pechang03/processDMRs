from flask import jsonify
from app.utils.extensions import app
from app.database.connection import get_db_engine
from sqlalchemy.orm import Session
from app.database.models import Timepoint

@app.route('/api/timepoints', methods=['GET'])
def get_timepoints():
    """Get all timepoints from the database."""
    engine = get_db_engine()
    with Session(engine) as session:
        timepoints = session.query(Timepoint).all()
        return jsonify([{
            'id': t.id,
            'name': t.name,
            'description': t.description,
            'sheet_name': t.sheet_name
        } for t in timepoints])
