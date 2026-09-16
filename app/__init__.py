# app/__init__.py
# Erzeugt die Flask-App und initialisiert die Erweiterungen aus dem Unterricht:
# Flask-SQLAlchemy (ORM), Flask-Migrate (Alembic) und Flask-Login (Sessions)
import logging
from logging.handlers import RotatingFileHandler
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
# Nicht angemeldete Benutzer werden auf die Login-Seite umgeleitet
login.login_view = 'login'
login.login_message = 'Bitte melden Sie sich an, um diese Seite zu sehen.'

# Logging in eine rotierende Datei, wie im Unterricht (Kap. 8)
if not app.debug:
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/dbwe.log',
                                       maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('DBWE gestartet')

# Import am Ende, um zirkuläre Importe zu vermeiden (wie im Unterricht)
from app import routes, models, errors, api
