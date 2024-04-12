from flask import Flask
from flask_session import Session
from config import Config
from .nylas_helper.routes import nylas_blueprint

from flask import render_template_string
from flask_cors import CORS

def create_app():
    application = Flask(__name__)
    application.config.from_object(Config)
    application.secret_key = application.config['SECRET_KEY']
    
    
    Session(application)
    # CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}}, supports_credentials=True)
    CORS(application, supports_credentials=True)
    @application.route("/")
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
    
    
    application.register_blueprint(nylas_blueprint, url_prefix='/nylas')

    return application
