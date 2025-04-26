import json
import os
from app import app
from database import db
from models import Classroom

file_path = os.path.join(os.path.dirname(__file__), 'classrooms.txt')

with app.app_context():
    db.create_all()
    
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        exit(1)
    except json.JSONDecodeError:
        print("Invalid JSON format in the file.")
        exit(1)

    added = 0
    for item in data:
        # verify all required keys are present
        if not all(key in item for key in ['building', 'floor', 'classroom_number']):
            print(f"Missing keys in item: {item}")
            continue
        
        try:
            floor = int(item['floor'])
        except ValueError:
            print(f"Invalid floor value: {item['floor']}")
            continue
        
        classroom_number = item['classroom_number']
        
        # duplicate avoidance
        existing = Classroom.query.filter_by(classroom_number=classroom_number).first()
        if existing:
            print(f"Classroom {classroom_number} already exists.")
            continue
        
        classroom = Classroom(
            building=item['building'],
            floor=floor,
            classroom_number=classroom_number
        )
        db.session.add(classroom)
        added += 1

    # Commit changes to the database
    try:
        db.session.commit()
        print(f"Successfully added {added} classrooms.")
    except Exception as e:
        print(f"Error committing to database: {e}")
        db.session.rollback()