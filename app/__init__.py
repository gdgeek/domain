"""App package initialization - Flask application factory."""
from flask import Flask
from config import config


def create_app(config_name='default'):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    from app.extensions import db, migrate
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Register blueprints
    from app.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    from app.admin import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Root redirect
    @app.route('/')
    def index():
        from flask import redirect
        return redirect('/admin/')
    
    return app
