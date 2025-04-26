# file for initializing the database, outside of app.py to interfere less with app development
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()