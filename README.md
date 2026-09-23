# DBWE – Praxisarbeit DBWE

Webanwendung mit Flask + MySQL zur Verwaltung von Kochrezepten
(Portionsrechner, Bewertungen, REST-API).

## Lokal starten (Entwicklung, SQLite)
```
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # SECRET_KEY setzen, DATABASE_URL auskommentieren
flask db upgrade                  # Tabellen anlegen (Migrationen)
python seed.py                    # optional: Demo-Daten
flask run
```
Browser: http://localhost:5000

## Tests
```
python -m unittest discover -s tests -v
```

## API (kurz)
```
http -a anna:Test1234 POST http://localhost:5000/api/tokens
http GET http://localhost:5000/api/recipes "Authorization: Bearer <token>"
http GET "http://localhost:5000/api/recipes/1?portions=8" "Authorization: Bearer <token>"
```
Vollständige Dokumentation: siehe Praxisarbeit (PDF).

## Deployment
Siehe `deploy/` (MySQL-Setup, Supervisor, Nginx) 
