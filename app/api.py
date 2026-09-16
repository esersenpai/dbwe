# app/api.py
# RESTful Web-API (Kap. 14 im Unterricht) mit Flask-HTTPAuth
#
# Authentifizierung ohne Browser:
#   1. POST /api/tokens mit HTTP Basic Auth (Benutzername:Passwort) -> Token
#   2. Alle weiteren Aufrufe mit Header "Authorization: Bearer <token>"
from flask import request, url_for, abort
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
import sqlalchemy as sa
from app import app, db
from app.models import User, Recipe
from app.errors import api_error_response

basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth()


@basic_auth.verify_password
def verify_password(username, password):
    user = db.session.scalar(sa.select(User).where(User.username == username))
    if user and user.check_password(password):
        return user


@basic_auth.error_handler
def basic_auth_error(status):
    return api_error_response(status)


@token_auth.verify_token
def verify_token(token):
    return User.check_token(token) if token else None


@token_auth.error_handler
def token_auth_error(status):
    return api_error_response(status)


# --- Token holen / zurückgeben -----------------------------------------
@app.route('/api/tokens', methods=['POST'])
@basic_auth.login_required
def get_token():
    token = basic_auth.current_user().get_token()
    db.session.commit()
    return {'token': token}


@app.route('/api/tokens', methods=['DELETE'])
@token_auth.login_required
def revoke_token():
    token_auth.current_user().revoke_token()
    db.session.commit()
    return '', 204


# --- Rezepte (lesend) ---------------------------------------------------
@app.route('/api/recipes', methods=['GET'])
@token_auth.login_required
def get_recipes():
    """Liste aller Rezepte, paginiert. Optional ?user_id=<id> filtert nach
    Autor. Beispiel: GET /api/recipes?page=1&per_page=10"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    user_id = request.args.get('user_id', type=int)
    query = sa.select(Recipe).order_by(Recipe.created_at.desc())
    if user_id:
        query = query.where(Recipe.user_id == user_id)
    recipes = db.paginate(query, page=page, per_page=per_page,
                          error_out=False)
    data = {
        'items': [r.to_dict() for r in recipes.items],
        '_meta': {'page': page, 'per_page': per_page,
                  'total_pages': recipes.pages,
                  'total_items': recipes.total},
        '_links': {
            'self': url_for('get_recipes', page=page, per_page=per_page,
                            user_id=user_id),
            'next': url_for('get_recipes', page=page + 1, per_page=per_page,
                            user_id=user_id) if recipes.has_next else None,
            'prev': url_for('get_recipes', page=page - 1, per_page=per_page,
                            user_id=user_id) if recipes.has_prev else None
        }
    }
    return data


@app.route('/api/recipes/<int:id>', methods=['GET'])
@token_auth.login_required
def get_recipe(id):
    """Einzelnes Rezept inkl. Zutaten. Mit ?portions=<n> werden die
    Mengen durch den Portionsrechner skaliert (Geschäftslogik)."""
    recipe = db.get_or_404(Recipe, id)
    portions = request.args.get('portions', type=int)
    if portions is not None and not 1 <= portions <= 100:
        return api_error_response(400, 'portions muss zwischen 1 und 100 '
                                       'liegen')
    return recipe.to_dict(portions=portions)


# --- Rezept erfassen (schreibend, optional) -----------------------------
@app.route('/api/recipes', methods=['POST'])
@token_auth.login_required
def create_recipe():
    """Erzeugt ein Rezept aus JSON:
    {"title": "...", "instructions": "...", "portions": 4,
     "ingredients": [{"name": "Mehl", "amount": 250, "unit": "g"}]}"""
    from app.models import Ingredient
    data = request.get_json(silent=True) or {}
    for field in ('title', 'instructions', 'ingredients'):
        if field not in data:
            return api_error_response(400, 'Feld fehlt: ' + field)
    recipe = Recipe(title=data['title'],
                    description=data.get('description'),
                    instructions=data['instructions'],
                    portions=int(data.get('portions', 4)),
                    prep_time=data.get('prep_time'),
                    author=token_auth.current_user())
    for ing in data['ingredients']:
        if 'name' not in ing:
            return api_error_response(400, 'Zutat ohne name')
        recipe.ingredients.append(Ingredient(
            name=ing['name'], amount=ing.get('amount'), unit=ing.get('unit')))
    db.session.add(recipe)
    db.session.commit()
    return recipe.to_dict(), 201, {'Location': url_for('get_recipe',
                                                        id=recipe.id)}


# --- Benutzer (lesend) ---------------------------------------------------
@app.route('/api/users/<int:id>', methods=['GET'])
@token_auth.login_required
def get_user(id):
    user = db.get_or_404(User, id)
    include_email = user == token_auth.current_user()
    return user.to_dict(include_email=include_email)
