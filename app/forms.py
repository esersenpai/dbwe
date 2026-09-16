# app/forms.py
# Formulare mit Flask-WTF / WTForms inkl. Validierung (Kap. 4 + 6)
import sqlalchemy as sa
from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, BooleanField, SubmitField,
                     TextAreaField, IntegerField, SelectField)
from wtforms.validators import (DataRequired, ValidationError, Email,
                                EqualTo, Length, NumberRange, Optional)
from app import db
from app.models import User


class LoginForm(FlaskForm):
    username = StringField('Benutzername', validators=[DataRequired()])
    password = PasswordField('Passwort', validators=[DataRequired()])
    remember_me = BooleanField('Angemeldet bleiben')
    submit = SubmitField('Anmelden')


class RegistrationForm(FlaskForm):
    username = StringField('Benutzername',
                           validators=[DataRequired(), Length(3, 64)])
    email = StringField('E-Mail', validators=[DataRequired(), Email()])
    password = PasswordField('Passwort',
                             validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Passwort wiederholen',
                              validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrieren')

    # Eigene Validatoren: Benutzername und E-Mail müssen eindeutig sein
    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(
            User.username == username.data))
        if user is not None:
            raise ValidationError('Dieser Benutzername ist bereits vergeben.')

    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(
            User.email == email.data))
        if user is not None:
            raise ValidationError('Diese E-Mail-Adresse ist bereits '
                                  'registriert.')


class RecipeForm(FlaskForm):
    title = StringField('Titel', validators=[DataRequired(), Length(1, 120)])
    description = TextAreaField('Kurzbeschreibung',
                                validators=[Optional(), Length(max=500)])
    portions = IntegerField('Portionen',
                            validators=[DataRequired(),
                                        NumberRange(1, 100)], default=4)
    prep_time = IntegerField('Zubereitungszeit (Minuten)',
                             validators=[Optional(), NumberRange(1, 1440)])
    # Zutaten werden als Textzeilen "Menge;Einheit;Name" erfasst,
    # z.B. "250;g;Mehl" – einfache Lösung ohne JavaScript
    ingredients = TextAreaField(
        'Zutaten (pro Zeile: Menge;Einheit;Name, z.B. 250;g;Mehl)',
        validators=[DataRequired()])
    instructions = TextAreaField('Zubereitung', validators=[DataRequired()])
    submit = SubmitField('Speichern')

    def validate_ingredients(self, ingredients):
        # Geschäftslogik: jede Zeile prüfen, Menge muss eine Zahl sein
        for nr, line in enumerate(ingredients.data.splitlines(), start=1):
            if not line.strip():
                continue
            parts = [p.strip() for p in line.split(';')]
            if len(parts) != 3 or not parts[2]:
                raise ValidationError(
                    'Zeile {}: Format muss "Menge;Einheit;Name" sein.'.format(
                        nr))
            if parts[0]:
                try:
                    float(parts[0].replace(',', '.'))
                except ValueError:
                    raise ValidationError(
                        'Zeile {}: Menge "{}" ist keine Zahl.'.format(
                            nr, parts[0]))


class RatingForm(FlaskForm):
    stars = SelectField('Bewertung', coerce=int,
                        choices=[(5, '5 Sterne'), (4, '4 Sterne'),
                                 (3, '3 Sterne'), (2, '2 Sterne'),
                                 (1, '1 Stern')])
    comment = TextAreaField('Kommentar',
                            validators=[Optional(), Length(max=300)])
    submit = SubmitField('Bewerten')


class PortionForm(FlaskForm):
    portions = IntegerField('Portionen',
                            validators=[DataRequired(), NumberRange(1, 100)])
    submit = SubmitField('Umrechnen')


class EmptyForm(FlaskForm):
    # Leeres Formular nur mit CSRF-Token, z.B. für den Löschen-Button
    submit = SubmitField('Löschen')
