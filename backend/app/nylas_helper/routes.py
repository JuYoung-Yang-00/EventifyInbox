from flask import Blueprint, request, redirect, url_for, session, jsonify, Response
from nylas import Client
from config import Config
from nylas.models.auth import URLForAuthenticationConfig
from nylas.models.auth import CodeExchangeRequest
import os
import hashlib
import hmac
import json 


nylas_blueprint = Blueprint('nylas', __name__)

nylas = Client(
    api_key=Config.NYLAS_API_KEY,
    api_uri=Config.NYLAS_API_URI,
)

# AUTH
@nylas_blueprint.route("/", methods=["GET"])
def login():
  if session.get("grant_id") is None:
    config = URLForAuthenticationConfig({"client_id": Config.NYLAS_CLIENT_ID, 
        "redirect_uri" : "https://api.eventifyinbox.com/nylas/callback"})

    url = nylas.auth.url_for_oauth2(config)

    return redirect(url)
  else:
    return redirect("https://eventifyinbox.com?nylasConnected=true")

@nylas_blueprint.route("/callback", methods=["GET"])
def authorized():
  if session.get("grant_id") is None:
    code = request.args.get("code")
    exchangeRequest = CodeExchangeRequest({
      "redirect_uri": "https://api.eventifyinbox.com/nylas/callback",
      "code": code,
      "client_id": Config.NYLAS_CLIENT_ID
    })
    exchange = nylas.auth.exchange_code_for_token(exchangeRequest)
    session["grant_id"] = exchange.grant_id
    
    return redirect("https://eventifyinbox.com?nylasConnected=true")


# EMAIL
@nylas_blueprint.route("/recent-emails", methods=["GET"])
def recent_emails():
  query_params = {"limit": 20}

  try:
    messages, _, _ = nylas.messages.list(session["grant_id"], query_params)

    return jsonify(messages)
  except Exception as e:
    return f'{e}' 


# CALENDAR
@nylas_blueprint.route("/primary-calendar", methods=["GET"])
def primary_calendar():
  query_params = {"limit": 10}
  try:
    calendars, _, _ = nylas.calendars.list(session["grant_id"], query_params)

    for primary in calendars:
      if primary.is_primary is True:
        session["calendar"] = primary.id
        
      return redirect("https://api.eventifyinbox.com/nylas/list-events")
  except Exception as e:
    return f'{e}'   

@nylas_blueprint.route("/list-events", methods=["GET"])
def list_events():
    if "calendar" not in session:
        # Connect to primary calendar first if not connected
        primary_calendar_response = primary_calendar()
        if primary_calendar_response.status_code != 200:
            return primary_calendar_response
    
    try:
        query_params = {"calendar_id": session["calendar"], "limit": 10}
        events = nylas.events.list(session["grant_id"], query_params=query_params)
        return jsonify(events)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

  
# WEBHOOK
def verify_nylas_signature(data, signature, webhook_secret):
    if not signature:
        return False
    expected_signature = hmac.new(webhook_secret.encode(), data, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected_signature, signature)


@nylas_blueprint.route("/webhook", methods=['GET', 'POST'])
def nylas_webhook():
    if request.method == "GET":
        challenge = request.args.get("challenge")
        if challenge:
            return Response(challenge, mimetype='text/plain')

    webhook_secret = os.getenv('WEBHOOK_SECRET')
    if not webhook_secret:
        print("Webhook secret not configured.")
        return "Webhook secret not configured.", 500

    signature = request.headers.get('X-Nylas-Signature')
    if not verify_nylas_signature(request.get_data(as_text=True).encode(), signature, webhook_secret):
        print("Signature verification failed.")
        return "Signature verification failed!", 401

    data = request.get_json(silent=True)
    if data:
        # send_notification_email(data) 
        print("Valid data received:", data)
        return jsonify(success=True), 200
    else:
        print("Invalid JSON data.")
        return "Invalid JSON data", 400





# Function to send an email notification with the webhook data
def send_notification_email(data):
    body = {
        "subject": "New Email Received via Webhook",
        "body": f"Received new email data: {json.dumps(data)}",  # Include the received data in the email body
        "to": [{"email": "toolbox.jyy@gmail.com"}]  # Sending to the admin email
    }
    try:
        nylas.messages.send(**body)
        print("Notification email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

