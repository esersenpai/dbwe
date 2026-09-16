# app/errors.py
# Fehlerbehandlung für Browser (HTML-Seiten) und API (JSON)
from flask import render_template, request
from werkzeug.http import HTTP_STATUS_CODES
from app import app, db


def api_error_response(status_code, message=None):
    payload = {'error': HTTP_STATUS_CODES.get(status_code, 'Unknown error')}
    if message:
        payload['message'] = message
    return payload, status_code


def wants_json():
    # API-Aufrufe (Pfad /api/...) erhalten JSON statt HTML
    return request.path.startswith('/api/')


@app.errorhandler(403)
def forbidden_error(error):
    if wants_json():
        return api_error_response(403)
    return render_template('error.html', code=403,
                           message='Zugriff verweigert.'), 403


@app.errorhandler(404)
def not_found_error(error):
    if wants_json():
        return api_error_response(404)
    return render_template('error.html', code=404,
                           message='Seite nicht gefunden.'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    if wants_json():
        return api_error_response(500)
    return render_template('error.html', code=500,
                           message='Interner Fehler.'), 500
