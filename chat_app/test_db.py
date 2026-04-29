import sys
import os

# Ensure the app context is available
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, Flora
with app.app_context():
    try:
        db.create_all()
        # Check if flora table exists
        floras = Flora.query.all()
        print(f"Floras in DB: {len(floras)}")
    except Exception as e:
        print(f"Error: {e}")
