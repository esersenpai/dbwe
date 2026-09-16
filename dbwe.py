# dbwe.py
# Einstiegspunkt der Anwendung (FLASK_APP=dbwe.py, gunicorn dbwe:app)
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import app, db
from app.models import User, Recipe, Ingredient, Rating


@app.shell_context_processor
def make_shell_context():
    # Stellt die wichtigsten Objekte in der 'flask shell' zur Verfügung
    return {'sa': sa, 'so': so, 'db': db, 'User': User, 'Recipe': Recipe,
            'Ingredient': Ingredient, 'Rating': Rating}
