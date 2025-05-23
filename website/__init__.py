from flask import Flask, send_from_directory, redirect, url_for, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
from flask_login import LoginManager
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()

# Sätt sökvägen till React build-mappen
REACT_BUILD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../frontend/build")

def create_app():
    app = Flask(__name__, static_folder=REACT_BUILD_DIR, static_url_path="/")

    # Flask-konfiguration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.config["SESSION_TYPE"] = "filesystem"
    app.config["SESSION_FILE_DIR"] = os.path.join(os.getcwd(), "flask_sessions")  # Spara sessioner här
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_USE_SIGNER"] = True
    app.config["SESSION_COOKIE_HTTPONLY"] = True  # För säkerhet
    app.config["SESSION_COOKIE_SAMESITE"] = "None"  # Tillåt cookies över domäner
    app.config["SESSION_COOKIE_SECURE"] = False  # Måste vara False om du testar lokalt

    Session(app)

    # Session directory initialiseras, håller koll på användarens inloggningsstatus
    session_dir = os.path.join(os.getcwd(), 'flask_session')
    os.makedirs(session_dir, exist_ok=True)
    app.config['SESSION_FILE_DIR'] = session_dir

    db.init_app(app)

    # Flask-Login konfiguration
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Tillåter React frontend att göra API-anrop till Flask
    CORS(app,
    resources={r"/*": {"origins": ["http://localhost:3000"]}},
    supports_credentials=True,
    expose_headers=["Set-Cookie"],
    allow_headers=["Content-Type", "Authorization"]
    )

    # Importera och registrera Blueprints
    from .views import views
    app.register_blueprint(views, url_prefix='/')

    from .google_auth import google_bp, oauth_routes
    app.register_blueprint(google_bp, url_prefix='/login')
    app.register_blueprint(oauth_routes, url_prefix='/')

    from .profile import show_profile
    app.register_blueprint(show_profile, url_prefix='/')

    from .models import User
    from . import db_events

    with app.app_context():
        db.drop_all()
        db.create_all()
        from .mock_data import add_mock_data
        add_mock_data()

    from .auth import auth
    app.register_blueprint(auth, url_prefix='/')

    # @login_manager.user_loader
    # def load_user(user_id):
    #     if user_id is None:
    #         return None
    #     return User.query.get(int(user_id))

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_react(path):
        full_path = os.path.join(REACT_BUILD_DIR, path)

        # Om filen finns, serva den
        if os.path.exists(full_path):
            return send_from_directory(REACT_BUILD_DIR, path)

        # Annars returnera index.html (för att stödja React Router)
        return send_from_directory(REACT_BUILD_DIR, 'index.html')

    return app
