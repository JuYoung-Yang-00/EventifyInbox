from flask import Flask
from flask_session import Session
from config import Config
from .nylas_helper.routes import nylas_blueprint

from flask import render_template_string
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.secret_key = app.config['SECRET_KEY']
    
    
    Session(app)
    # CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}}, supports_credentials=True)
    CORS(app, supports_credentials=True)
    @app.route("/")
    def home():
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Welcome</title>
        </head>
        <body>
            <h1>Welcome to Backend</h1>
            <form action="/nylas">
                <input type="submit" value="Connect to Nylas" />
            </form>
        </body>
        </html>
        """)
    
    
    app.register_blueprint(nylas_blueprint, url_prefix='/nylas')

    return app
