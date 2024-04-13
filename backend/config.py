from dotenv import load_dotenv
import os
from dotenv import load_dotenv


load_dotenv()

class Config:
    SESSION_PERMANENT = False
    SESSION_TYPE = "filesystem"
    NYLAS_API_KEY = os.getenv("NYLAS_API_KEY")
    NYLAS_API_URI = os.getenv("NYLAS_API_URI")
    NYLAS_CLIENT_ID = os.getenv("NYLAS_CLIENT_ID")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    SECRET_KEY = os.getenv("SECRET_KEY")
    WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")