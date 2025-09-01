from flask import Flask
from config import Config
from .db import db, migrate
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)

    from app.routes.auth import auth_bp
    from app.routes.lojas import lojas_bp
    from app.routes.api import api_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(lojas_bp, url_prefix='/lojas')
    # O prefixo da URL agora inclui o path da loja, que será tratado no blueprint.
    app.register_blueprint(api_bp, url_prefix='/<loja_path>')

    from app import models

    return app
