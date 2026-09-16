# seed.py – legt Demo-Daten an (Testuser + zwei Rezepte)
# Ausführen: python seed.py
from app import app, db
from app.models import User, Recipe, Ingredient, Rating

with app.app_context():
    if User.query.first():
        print('Datenbank enthält bereits Daten – nichts gemacht.')
    else:
        anna = User(username='anna', email='anna@example.com')
        anna.set_password('Test1234')
        ben = User(username='ben', email='ben@example.com')
        ben.set_password('Test1234')
        r1 = Recipe(title='Pancakes', description='Fluffige Pfannkuchen zum Frühstück',
                    instructions='Mehl, Zucker und Backpulver mischen.\nEier und Milch dazugeben und glatt rühren.\nIn der Pfanne portionsweise goldbraun backen.',
                    portions=4, prep_time=25, author=anna)
        r1.ingredients = [Ingredient(name='Mehl', amount=200, unit='g'),
                          Ingredient(name='Zucker', amount=2, unit='EL'),
                          Ingredient(name='Backpulver', amount=1, unit='TL'),
                          Ingredient(name='Eier', amount=2),
                          Ingredient(name='Milch', amount=300, unit='ml')]
        r2 = Recipe(title='Tomatensauce', description='Einfache Sauce für Pasta',
                    instructions='Zwiebel und Knoblauch in Olivenöl andünsten.\nTomaten dazugeben, 20 Minuten köcheln, würzen.',
                    portions=2, prep_time=30, author=ben)
        r2.ingredients = [Ingredient(name='Zwiebel', amount=1),
                          Ingredient(name='Knoblauchzehen', amount=2),
                          Ingredient(name='Dosentomaten', amount=400, unit='g'),
                          Ingredient(name='Olivenöl', amount=2, unit='EL')]
        db.session.add_all([anna, ben, r1, r2])
        db.session.add(Rating(stars=5, comment='Sehr lecker!', user=ben, recipe=r1))
        db.session.commit()
        print('Demo-Daten angelegt: User anna/ben (Passwort Test1234)')
