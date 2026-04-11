import os
import unittest
from datetime import date, timedelta
from unittest.mock import patch

import modules
from modules.scrap import get_table_data_from_page, seed_bet_data
from modules.models import BettingOpportunity, User, db


class FlaskAppTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = os.path.join(os.getcwd(), "instance", "test_data")
        os.makedirs(cls.test_dir, exist_ok=True)
        cls.db_path = os.path.join(cls.test_dir, "test_app.db")
        cls.db_uri = f"sqlite:///{cls.db_path.replace(os.sep, '/')}"
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)

        class FakeConfig:
            def __init__(self, _config_file):
                self.config_data = {"finance": {"automatic_dollar_value": False}}

            @property
            def database_uri(self):
                return cls.db_uri

            @property
            def secret_key(self):
                return "test-secret-key"

            @property
            def buy_exchanges(self):
                return ""

            @property
            def sell_exchanges(self):
                return ""

            @property
            def email(self):
                return "tests@example.com"

            @property
            def dollar_value(self):
                return 5.0

        cls.config_patcher = patch.object(modules, "Config", FakeConfig)
        cls.config_patcher.start()

        cls.app, cls.config = modules.create_app()
        cls.app.config.update(
            TESTING=True,
            WTF_CSRF_ENABLED=False,
            SQLALCHEMY_DATABASE_URI=cls.db_uri,
        )

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()
        cls.config_patcher.stop()

    def setUp(self):
        self.client = self.app.test_client()
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.create_all()

            admin = User(
                username="admin",
                is_admin=True,
                date_expiry=date.today() + timedelta(days=30),
            )
            admin.set_password("admin123")

            regular = User(
                username="user",
                is_admin=False,
                date_expiry=date.today() + timedelta(days=30),
            )
            regular.set_password("user123")

            expired = User(
                username="expired",
                is_admin=False,
                date_expiry=date.today() - timedelta(days=1),
            )
            expired.set_password("expired123")

            db.session.add_all([admin, regular, expired])

            db.session.add_all(
                [
                    BettingOpportunity(
                        profit=3.5,
                        age="10m",
                        bookmaker1="Betano",
                        sport1="Futebol",
                        time1="2026-04-09 12:00",
                        event1="Time A x Time B",
                        event_link1="https://example.com/event-1",
                        league1="Serie A",
                        market1="1x2",
                        odds1=2.10,
                        stake_limit1="100",
                        bookmaker2="Stake",
                        sport2="Futebol",
                        time2="2026-04-09 12:00",
                        event2="Time A x Time B",
                        event_link2="https://example.com/event-1-b",
                        league2="Serie A",
                        market2="1x2",
                        odds2=1.95,
                        stake_limit2="90",
                    ),
                    BettingOpportunity(
                        profit=1.2,
                        age="30m",
                        bookmaker1="Superbet",
                        sport1="Basquete",
                        time1="2026-04-10 15:30",
                        event1="Time C x Time D",
                        event_link1="https://example.com/event-2",
                        league1="NBB",
                        market1="Total",
                        odds1=1.80,
                        stake_limit1="150",
                    ),
                ]
            )
            db.session.commit()

    def login(self, username, password, follow_redirects=True):
        return self.client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=follow_redirects,
        )

    def test_login_page_loads(self):
        response = self.client.get("/login")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"", response.data)

    def test_home_requires_authentication(self):
        response = self.client.get("/", follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    def test_active_user_can_login_and_access_dashboard(self):
        login_response = self.login("admin", "admin123")
        dashboard_response = self.client.get("/")

        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertIn(b"FILTROS", dashboard_response.data)

    def test_expired_user_sees_plan_expired_page(self):
        response = self.login("expired", "expired123")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Plano Expirado", response.data)

    def test_admin_page_requires_admin_role(self):
        self.login("user", "user123")
        response = self.client.get("/users", follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertIn("/", response.headers["Location"])

    def test_admin_can_open_user_management_page(self):
        self.login("admin", "admin123")
        response = self.client.get("/users")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Gerenciar Usu", response.data)

    def test_filters_endpoint_returns_available_options(self):
        response = self.client.get("/api/filters")
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertIn("Betano", data["bookmakers"])
        self.assertIn("Superbet", data["bookmakers"])
        self.assertIn("Futebol", data["sports"])
        self.assertEqual(data["min_profit"], 1.2)
        self.assertEqual(data["max_profit"], 3.5)

    def test_opportunities_endpoint_supports_filters_and_pagination(self):
        response = self.client.get(
            "/api/opportunities?bookmaker=Betano&sport=Futebol&min_profit=2&page=1&per_page=20"
        )
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["total"], 1)
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(data["items"][0]["event1"], "Time A x Time B")
        self.assertEqual(data["items"][0]["bookmaker1"], "Betano")

    def test_not_found_page_uses_custom_template(self):
        response = self.client.get("/route-that-does-not-exist")

        self.assertEqual(response.status_code, 404)
        self.assertIn(b"Erro 404", response.data)

    def test_betfair_scraping_returns_normalized_data_and_persists(self):
        bets = modules.asyncio.run(get_table_data_from_page())

        self.assertTrue(bets)
        self.assertGreaterEqual(len(bets[0].bookmakers), 1)

        with self.app.app_context():
            db.session.query(BettingOpportunity).delete()
            db.session.commit()

        stored = modules.asyncio.run(seed_bet_data(self.app, bets))

        self.assertGreaterEqual(stored, 1)
        with self.app.app_context():
            opportunity = BettingOpportunity.query.first()
            self.assertIsNotNone(opportunity)
            self.assertEqual(opportunity.age, "betfair-api")


if __name__ == "__main__":
    unittest.main()
