# app/models.py
# Datenmodell der Anwendung (SQLAlchemy 2.0 Schreibweise wie im Unterricht)
#
# Tabellen: user, recipe, ingredient, rating
# Beziehungen: User 1:n Recipe, Recipe 1:n Ingredient,
#              User n:m Recipe über Rating (Bewertung mit Kommentar)
from datetime import datetime, timezone, timedelta
from typing import Optional
import secrets
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask import url_for
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login


class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True,
                                                unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True,
                                             unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    created_at: so.Mapped[datetime] = so.mapped_column(
        default=lambda: datetime.now(timezone.utc))
    # API-Token (Kap. 14.10 im Unterricht)
    token: so.Mapped[Optional[str]] = so.mapped_column(
        sa.String(32), index=True, unique=True)
    token_expiration: so.Mapped[Optional[datetime]]

    recipes: so.WriteOnlyMapped['Recipe'] = so.relationship(
        back_populates='author')
    ratings: so.WriteOnlyMapped['Rating'] = so.relationship(
        back_populates='user')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    # Passwort wird nie im Klartext gespeichert, sondern als Hash
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def recipe_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.recipes.select().subquery())
        return db.session.scalar(query)

    # --- API-Token: erzeugen, widerrufen, prüfen ---------------------------
    def get_token(self, expires_in=3600):
        now = datetime.now(timezone.utc)
        if self.token and self.token_expiration.replace(
                tzinfo=timezone.utc) > now + timedelta(seconds=60):
            return self.token
        self.token = secrets.token_hex(16)
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        return self.token

    def revoke_token(self):
        self.token_expiration = datetime.now(timezone.utc) - timedelta(
            seconds=1)

    @staticmethod
    def check_token(token):
        user = db.session.scalar(sa.select(User).where(User.token == token))
        if user is None or user.token_expiration.replace(
                tzinfo=timezone.utc) < datetime.now(timezone.utc):
            return None
        return user

    # Darstellung als Dictionary für das REST-API (ohne Passwort/Token)
    def to_dict(self, include_email=False):
        data = {
            'id': self.id,
            'username': self.username,
            'recipe_count': self.recipe_count(),
            '_links': {
                'self': url_for('get_user', id=self.id),
                'recipes': url_for('get_recipes', user_id=self.id)
            }
        }
        if include_email:
            data['email'] = self.email
        return data


@login.user_loader
def load_user(id):
    # Wird von Flask-Login benutzt, um den User der Session zu laden
    return db.session.get(User, int(id))


class Recipe(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    title: so.Mapped[str] = so.mapped_column(sa.String(120), index=True)
    description: so.Mapped[Optional[str]] = so.mapped_column(sa.String(500))
    instructions: so.Mapped[str] = so.mapped_column(sa.Text)
    # Anzahl Portionen, auf die sich die Mengenangaben beziehen
    portions: so.Mapped[int] = so.mapped_column(default=4)
    prep_time: so.Mapped[Optional[int]]  # Zubereitungszeit in Minuten
    created_at: so.Mapped[datetime] = so.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc))
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id),
                                               index=True)

    author: so.Mapped[User] = so.relationship(back_populates='recipes')
    # Zutaten werden mit dem Rezept gelöscht (cascade)
    ingredients: so.Mapped[list['Ingredient']] = so.relationship(
        back_populates='recipe', cascade='all, delete-orphan',
        order_by='Ingredient.id')
    ratings: so.Mapped[list['Rating']] = so.relationship(
        back_populates='recipe', cascade='all, delete-orphan')

    def __repr__(self):
        return '<Recipe {}>'.format(self.title)

    # --- Geschäftslogik -----------------------------------------------------
    def scaled_ingredients(self, wanted_portions):
        """Portionsrechner: skaliert alle Mengen auf die gewünschte
        Anzahl Portionen (Dreisatz). Gibt eine Liste von Tupeln zurück."""
        factor = wanted_portions / self.portions
        result = []
        for ing in self.ingredients:
            amount = round(ing.amount * factor, 2) if ing.amount else None
            result.append((ing, amount))
        return result

    def average_rating(self):
        """Durchschnittliche Bewertung (1-5 Sterne) oder None."""
        if not self.ratings:
            return None
        return round(sum(r.stars for r in self.ratings) / len(self.ratings),
                     1)

    def rating_by(self, user):
        """Gibt die Bewertung eines bestimmten Users zurück (oder None)."""
        for r in self.ratings:
            if r.user_id == user.id:
                return r
        return None

    def to_dict(self, portions=None):
        wanted = portions or self.portions
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'instructions': self.instructions,
            'portions': wanted,
            'prep_time': self.prep_time,
            'author': self.author.username,
            'created_at': self.created_at.replace(
                tzinfo=timezone.utc).isoformat(),
            'average_rating': self.average_rating(),
            'rating_count': len(self.ratings),
            'ingredients': [
                {'name': ing.name, 'amount': amount, 'unit': ing.unit}
                for ing, amount in self.scaled_ingredients(wanted)
            ],
            '_links': {
                'self': url_for('get_recipe', id=self.id),
                'author': url_for('get_user', id=self.user_id)
            }
        }
        return data


class Ingredient(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(80))
    amount: so.Mapped[Optional[float]]
    unit: so.Mapped[Optional[str]] = so.mapped_column(sa.String(20))
    recipe_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Recipe.id),
                                                 index=True)

    recipe: so.Mapped[Recipe] = so.relationship(back_populates='ingredients')

    def __repr__(self):
        return '<Ingredient {} {} {}>'.format(self.amount, self.unit,
                                              self.name)


class Rating(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    stars: so.Mapped[int]  # 1 bis 5
    comment: so.Mapped[Optional[str]] = so.mapped_column(sa.String(300))
    created_at: so.Mapped[datetime] = so.mapped_column(
        default=lambda: datetime.now(timezone.utc))
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id),
                                               index=True)
    recipe_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Recipe.id),
                                                 index=True)
    # Ein User darf ein Rezept nur einmal bewerten
    __table_args__ = (sa.UniqueConstraint('user_id', 'recipe_id',
                                          name='uq_user_recipe'),)

    user: so.Mapped[User] = so.relationship(back_populates='ratings')
    recipe: so.Mapped[Recipe] = so.relationship(back_populates='ratings')

    def __repr__(self):
        return '<Rating {} stars>'.format(self.stars)
