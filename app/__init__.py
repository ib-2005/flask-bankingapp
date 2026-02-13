from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate 
from app.extensions import db, login_manager
from flask_mail import Mail

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate = Migrate(app, db)
    
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    from app.routes import bp 
    app.register_blueprint(bp)
    
    return app