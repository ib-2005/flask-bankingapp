from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate 
from app.extensions import db, login_manager
from app.models import User, Account, Transaction, Session, AccountType, VerificationCode, TransactionStatus, TransactionType, VerificationCodePurpose
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
import sqlalchemy as sa 

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate = Migrate(app, db)
    
    csrf = CSRFProtect()
    csrf.init_app(app)
    
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    from app.routes import bp 
    app.register_blueprint(bp)

    @app.shell_context_processor
    def make_shell_context():
        return {
            "db": db,
            "sa": sa,
            "User": User,
            "Account": Account,
            "Transaction": Transaction,
            "Session": Session,
            "AccountType": AccountType,
            "VerificationCode": VerificationCode,
            "TransactionStatus": TransactionStatus,
            "TransactionType": TransactionType,
            "VerificationCodePurpose": VerificationCodePurpose,
        }

    return app