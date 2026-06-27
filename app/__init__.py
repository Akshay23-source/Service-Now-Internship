from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import Config
import logging
from logging.handlers import RotatingFileHandler
import os

# Instantiate extension objects. 
# We declare these at the module level so they can be imported into other files (like routes or models),
# but they are not bound to a specific Flask application instance yet.
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

# Configure Flask-Login settings
# 'auth.login' tells Flask-Login where to redirect users if they try to access a @login_required route
login_manager.login_view = 'auth.login'
# CSS class for the default flash message category
login_manager.login_message_category = 'warning'

def create_app(config_class=Config):
    """
    Application Factory function. 
    It creates a new Flask app instance, loads configurations, initializes extensions,
    and registers blueprints.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with the newly created app instance
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Configure Rotating File Logging
    os.makedirs('logs', exist_ok=True)
    file_handler = RotatingFileHandler('logs/smartnotes.log', maxBytes=100000, backupCount=5)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('SmartNotes Pro application initialized successfully.')

    # Register blueprints (modular sections of the application)
    from app.auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import main_bp
    app.register_blueprint(main_bp)

    # Register custom error handlers
    register_error_handlers(app)

    return app

def register_error_handlers(app):
    from flask import render_template
    
    @app.errorhandler(400)
    def bad_request_error(error):
        app.logger.warning(f"Bad request (400): {error}")
        return render_template('errors/400.html', title='Bad Request'), 400

    @app.errorhandler(403)
    def forbidden_error(error):
        app.logger.warning(f"Access forbidden (403): {error}")
        return render_template('errors/403.html', title='Forbidden'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.info(f"Resource not found (404): {error}")
        return render_template('errors/404.html', title='Not Found'), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal server error (500): {error}")
        db.session.rollback()
        return render_template('errors/500.html', title='Server Error'), 500

