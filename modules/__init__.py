
import asyncio
import os
from threading import Thread
from flask import Flask, session, render_template
from .config import Config
from .models import db, User, BettingOpportunity, init_db
from .scrap import start_scraping
from flask_session import Session
from flask_login import LoginManager
from datetime import timedelta
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from .util import get_current_dollar_value, log
import time

login_manager = LoginManager()

def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    config = Config("config.toml")

    app.config['SQLALCHEMY_DATABASE_URI'] = config.database_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = config.secret_key
    app.config['SESSION_TYPE'] = 'filesystem'
    os.makedirs(app.instance_path, exist_ok=True)
    app.config['SESSION_FILE_DIR'] = os.path.join(app.instance_path, 'flask_session')
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
    app.config['BUY_EXCHANGES'] = config.buy_exchanges
    app.config['SELL_EXCHANGES'] = config.sell_exchanges
    app.config['EMAIL'] = config.email
    app.config['DOLLAR_VALUE'] = config.dollar_value

    db.init_app(app)
    Session(app)
    login_manager.init_app(app)
    login_manager.login_view = 'authentication.login'

    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["86400 per day", "3600 per hour"]
    )

    with app.app_context():
        init_db(app)  # Initialize database tables
    from modules.routes import api_bp   
    from .views.routes import views_bp
    from .socketio_custom import register_socketio_blueprint
    from .authentication import authentication_bp

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('home/page-404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('home/page-500.html'), 500
    app.register_blueprint(api_bp)
    app.register_blueprint(views_bp)
    app.register_blueprint(authentication_bp)
    register_socketio_blueprint(app)

    return app, config

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def start_background_tasks(app, config):
    def run_scraping():
        asyncio.run(start_scraping(app))

    def update_dollar_value():
        while True:
            with app.app_context():
                if config.config_data["finance"].get("automatic_dollar_value"):
                    dollar_value = get_current_dollar_value()
                    if dollar_value != 0:
                        app.config['DOLLAR_VALUE'] = dollar_value
                        log(f"Updated dollar value to: {dollar_value}", "warning")
                    else:
                        log("Failed to update dollar value", "danger")
            time.sleep(300)

    scraping_thread = Thread(target=run_scraping)
    scraping_thread.daemon = True  # Make thread daemon
    scraping_thread.start()

    dollar_update_thread = Thread(target=update_dollar_value)
    dollar_update_thread.daemon = True  # Make thread daemon
    dollar_update_thread.start()
