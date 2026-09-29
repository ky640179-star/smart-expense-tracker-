from flask import Flask
from config import Config
from extensions import db, login_manager, csrf

def create_app(config=Config):
    app = Flask(__name__)
    app.config.from_object(config)
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    from routes.auth import bp as auth_bp
    from routes.main import bp as main_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    with app.app_context():
        db.create_all()
    return app

if __name__ == "__main__":
    create_app().run(debug=True)
