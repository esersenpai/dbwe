# tests/test_app.py
# Automatisierte Tests mit unittest (Vorgehen wie im Unterricht, Kap. 9)
# Ausführen: python -m unittest -v
import os
os.environ['DATABASE_URL'] = 'sqlite://'  # In-Memory-DB, vor App-Import!
import unittest
from app import app, db
from app.models import User, Recipe, Ingredient, Rating


class DBWETests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.ctx = app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = app.test_client()
        self.u = User(username='anna', email='anna@example.com')
        self.u.set_password('geheim123')
        db.session.add(self.u)
        self.r = Recipe(title='Pancakes', instructions='Alles mischen.',
                        portions=4, author=self.u)
        self.r.ingredients = [Ingredient(name='Mehl', amount=200, unit='g'),
                              Ingredient(name='Eier', amount=2)]
        db.session.add(self.r)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    # T1: Passwort-Hashing
    def test_password_hashing(self):
        self.assertTrue(self.u.check_password('geheim123'))
        self.assertFalse(self.u.check_password('falsch'))

    # T2: Portionsrechner (Geschäftslogik)
    def test_portion_scaling(self):
        scaled = self.r.scaled_ingredients(2)
        self.assertEqual(scaled[0][1], 100)
        self.assertEqual(scaled[1][1], 1)

    # T3: Durchschnittsbewertung
    def test_average_rating(self):
        self.assertIsNone(self.r.average_rating())
        u2 = User(username='ben', email='ben@example.com')
        db.session.add(Rating(stars=4, user=u2, recipe=self.r))
        db.session.add(Rating(stars=5, user=self.u, recipe=self.r))
        db.session.commit()
        self.assertEqual(self.r.average_rating(), 4.5)

    # T4: Registrierung mit doppeltem Benutzernamen wird abgelehnt
    def test_register_duplicate_username(self):
        rv = self.client.post('/register', data={
            'username': 'anna', 'email': 'neu@example.com',
            'password': 'abcdef', 'password2': 'abcdef'})
        self.assertIn('bereits vergeben', rv.get_data(as_text=True))

    # T5: Geschützte Seite verlangt Login
    def test_login_required(self):
        rv = self.client.get('/recipe/new')
        self.assertEqual(rv.status_code, 302)
        self.assertIn('/login', rv.headers['Location'])

    # T6: API ohne Token liefert 401
    def test_api_requires_token(self):
        rv = self.client.get('/api/recipes')
        self.assertEqual(rv.status_code, 401)

    # T7: Token holen und Rezept lesen (skaliert)
    def test_api_token_and_recipe(self):
        rv = self.client.post('/api/tokens', auth=('anna', 'geheim123'))
        self.assertEqual(rv.status_code, 200)
        token = rv.get_json()['token']
        rv = self.client.get('/api/recipes/1?portions=8',
                             headers={'Authorization': 'Bearer ' + token})
        self.assertEqual(rv.status_code, 200)
        data = rv.get_json()
        self.assertEqual(data['portions'], 8)
        self.assertEqual(data['ingredients'][0]['amount'], 400)

    # T8: Fremdes Rezept darf nicht gelöscht werden
    def test_delete_foreign_recipe_forbidden(self):
        u2 = User(username='ben', email='ben@example.com')
        u2.set_password('x')
        db.session.add(u2)
        db.session.commit()
        self.client.post('/login', data={'username': 'ben', 'password': 'x'})
        rv = self.client.post('/recipe/1/delete')
        self.assertEqual(rv.status_code, 403)


if __name__ == '__main__':
    unittest.main(verbosity=2)
