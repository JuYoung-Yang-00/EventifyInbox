from flask import Flask
from flask_session import Session
from config import Config
from .nylas_helper.routes import nylas_blueprint

from flask import render_template_string
from flask_cors import CORS
from pymongo import MongoClient, errors

def create_app():
    application = Flask(__name__)
    application.config.from_object(Config)
    application.secret_key = application.config['SECRET_KEY']
    
    Session(application)
    CORS(application, supports_credentials=True)
    
    # MongoDB Connection
    try:
        password = application.config['MONGODB_PASSWORD']
        # mongo_uri = f"mongodb+srv://juyoungyang00:{password}@cluster0.1hvpjjc.mongodb.net/"
        mongo_uri= f"mongodb+srv://juyoungyang00:{password}@cluster0.1hvpjjc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)  # 5 second timeout
        client.server_info()  # Forces a call to check if connected.
        application.db = client.eventifyinbox
        print("MongoDB is connected successfully.")
    except errors.ServerSelectionTimeoutError as err:
        # Handle errors if MongoDB is unreachable
        print("Failed to connect to MongoDB:", err)
        raise ConnectionError("Database connection failed.")
    
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
