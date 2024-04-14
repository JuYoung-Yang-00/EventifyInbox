from flask import Flask
from flask_session import Session
from config import Config
from .nylas_helper.routes import nylas_blueprint

from flask import render_template_string
from flask_cors import CORS
from pymongo import MongoClient
import os

def create_app():
    application = Flask(__name__)
    application.config.from_object(Config)
    application.secret_key = application.config['SECRET_KEY']
    
    Session(application)
    CORS(application, supports_credentials=True)
    
    mongo_uri = f"mongodb+srv://juyoungyang00:{application.config['MONGODB_PASSWORD']}@cluster0.1hvpjjc.mongodb.net/"

    client = MongoClient(mongo_uri)
    application.db = client.eventifyinbox
    
    @application.route("/")
    def home():
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Welcome</title>
        </head>
        <body>
            <h1>Welcome to Backend for Eventify Inbox!</h1>
        </body>
        </html>
        """)
    
    
    application.register_blueprint(nylas_blueprint, url_prefix='/nylas')

    return application
