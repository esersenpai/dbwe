# config.py
# Konfiguration der Flask-App (Vorgehen wie im Unterricht, Kap. 5 + 13)
import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
# Geheime Werte (SECRET_KEY, DATABASE_URL) werden aus der Datei .env gelesen
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    # Schlüssel für Session-Cookies und CSRF-Token von Flask-WTF
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'nur-fuer-entwicklung-aendern'
    # Produktion: DATABASE_URL zeigt auf MySQL (mysql+pymysql://...)
    # Entwicklung: Fallback auf eine lokale SQLite-Datei app.db
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Anzahl Rezepte pro Seite (Paginierung)
    RECIPES_PER_PAGE = 6
