# app/routes.py
# View-Funktionen für die Weboberfläche (Browser)
from urllib.parse import urlsplit
from flask import render_template, flash, redirect, url_for, request, abort
from flask_login import current_user, login_user, logout_user, login_required
import sqlalchemy as sa
from app import app, db
from app.forms import (LoginForm, RegistrationForm, RecipeForm, RatingForm,
                       PortionForm, EmptyForm)
from app.models import User, Recipe, Ingredient, Rating


def parse_ingredients(text):
    """Wandelt die Zutaten-Textzeilen 'Menge;Einheit;Name' in
    Ingredient-Objekte um (Format wurde bereits im Formular validiert)."""
    result = []
    for line in text.splitlines():
        if not line.strip():
            continue
        amount, unit, name = [p.strip() for p in line.split(';')]
        amount = float(amount.replace(',', '.')) if amount else None
        result.append(Ingredient(name=name, amount=amount, unit=unit or None))
    return result


def ingredients_to_text(recipe):
    """Umkehrung von parse_ingredients() für das Bearbeiten-Formular."""
    lines = []
    for ing in recipe.ingredients:
        amount = ('%g' % ing.amount) if ing.amount is not None else ''
        lines.append('{};{};{}'.format(amount, ing.unit or '', ing.name))
    return '\n'.join(lines)


# --- Startseite / Rezeptliste --------------------------------------------
@app.route('/')
@app.route('/index')
def index():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '', type=str).strip()
    query = sa.select(Recipe).order_by(Recipe.created_at.desc())
    if q:
        # Einfache Suche im Titel und in der Beschreibung
        query = query.where(sa.or_(Recipe.title.ilike('%' + q + '%'),
                                   Recipe.description.ilike('%' + q + '%')))
    recipes = db.paginate(query, page=page,
                          per_page=app.config['RECIPES_PER_PAGE'],
                          error_out=False)
    next_url = url_for('index', page=recipes.next_num, q=q) \
        if recipes.has_next else None
    prev_url = url_for('index', page=recipes.prev_num, q=q) \
        if recipes.has_prev else None
    return render_template('index.html', title='Rezepte',
                           recipes=recipes.items, q=q,
                           next_url=next_url, prev_url=prev_url)


# --- Registrierung / Login / Logout ---------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registrierung erfolgreich, Sie können sich jetzt anmelden.')
        return redirect(url_for('login'))
    return render_template('register.html', title='Registrieren', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash('Benutzername oder Passwort ist falsch.')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        # Nach dem Login zurück zur ursprünglich gewünschten Seite
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Anmelden', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


# --- Rezepte: anzeigen, erfassen, bearbeiten, löschen ---------------------
@app.route('/recipe/<int:id>', methods=['GET', 'POST'])
def recipe(id):
    recipe = db.get_or_404(Recipe, id)
    portion_form = PortionForm()
    rating_form = RatingForm()
    # Portionsrechner: gewünschte Portionen aus URL-Parameter oder Standard
    wanted = request.args.get('portions', recipe.portions, type=int)
    if portion_form.validate_on_submit() and portion_form.submit.data:
        return redirect(url_for('recipe', id=id,
                                portions=portion_form.portions.data))
    portion_form.portions.data = wanted
    return render_template('recipe.html', title=recipe.title, recipe=recipe,
                           wanted=wanted,
                           ingredients=recipe.scaled_ingredients(wanted),
                           portion_form=portion_form,
                           rating_form=rating_form, delete_form=EmptyForm())


@app.route('/recipe/new', methods=['GET', 'POST'])
@login_required
def new_recipe():
    form = RecipeForm()
    if form.validate_on_submit():
        recipe = Recipe(title=form.title.data,
                        description=form.description.data,
                        instructions=form.instructions.data,
                        portions=form.portions.data,
                        prep_time=form.prep_time.data,
                        author=current_user)
        recipe.ingredients = parse_ingredients(form.ingredients.data)
        db.session.add(recipe)
        db.session.commit()
        flash('Rezept wurde gespeichert.')
        return redirect(url_for('recipe', id=recipe.id))
    return render_template('edit_recipe.html', title='Neues Rezept',
                           form=form)


@app.route('/recipe/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_recipe(id):
    recipe = db.get_or_404(Recipe, id)
    if recipe.author != current_user:
        abort(403)  # Nur der Autor darf sein Rezept bearbeiten
    form = RecipeForm()
    if form.validate_on_submit():
        recipe.title = form.title.data
        recipe.description = form.description.data
        recipe.instructions = form.instructions.data
        recipe.portions = form.portions.data
        recipe.prep_time = form.prep_time.data
        recipe.ingredients = parse_ingredients(form.ingredients.data)
        db.session.commit()
        flash('Änderungen wurden gespeichert.')
        return redirect(url_for('recipe', id=recipe.id))
    elif request.method == 'GET':
        form.title.data = recipe.title
        form.description.data = recipe.description
        form.instructions.data = recipe.instructions
        form.portions.data = recipe.portions
        form.prep_time.data = recipe.prep_time
        form.ingredients.data = ingredients_to_text(recipe)
    return render_template('edit_recipe.html', title='Rezept bearbeiten',
                           form=form)


@app.route('/recipe/<int:id>/delete', methods=['POST'])
@login_required
def delete_recipe(id):
    recipe = db.get_or_404(Recipe, id)
    if recipe.author != current_user:
        abort(403)
    form = EmptyForm()
    if form.validate_on_submit():
        db.session.delete(recipe)
        db.session.commit()
        flash('Rezept wurde gelöscht.')
    return redirect(url_for('index'))


# --- Bewertungen ----------------------------------------------------------
@app.route('/recipe/<int:id>/rate', methods=['POST'])
@login_required
def rate_recipe(id):
    recipe = db.get_or_404(Recipe, id)
    form = RatingForm()
    if form.validate_on_submit():
        if recipe.author == current_user:
            flash('Eigene Rezepte können nicht bewertet werden.')
            return redirect(url_for('recipe', id=id))
        rating = recipe.rating_by(current_user)
        if rating is None:
            rating = Rating(user=current_user, recipe=recipe)
            db.session.add(rating)
        # Bestehende Bewertung wird überschrieben (nur eine pro User)
        rating.stars = form.stars.data
        rating.comment = form.comment.data
        db.session.commit()
        flash('Vielen Dank für Ihre Bewertung.')
    return redirect(url_for('recipe', id=id))


# --- Benutzerprofil -------------------------------------------------------
@app.route('/user/<username>')
@login_required
def user(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    query = user.recipes.select().order_by(Recipe.created_at.desc())
    recipes = db.session.scalars(query).all()
    return render_template('user.html', title=user.username, user=user,
                           recipes=recipes)
