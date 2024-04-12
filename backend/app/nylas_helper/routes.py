from flask import Blueprint, request, redirect, url_for, session, jsonify
from nylas import Client
from config import Config
from nylas.models.auth import URLForAuthenticationConfig
from nylas.models.auth import CodeExchangeRequest

nylas_blueprint = Blueprint('nylas', __name__)

nylas = Client(
    api_key=Config.NYLAS_API_KEY,
    api_uri=Config.NYLAS_API_URI,
)


@nylas_blueprint.route("/", methods=["GET"])
def login():
  if session.get("grant_id") is None:
    config = URLForAuthenticationConfig({"client_id": Config.NYLAS_CLIENT_ID, 
        "redirect_uri" : "http://127.0.0.1:5000/nylas/callback"})

    url = nylas.auth.url_for_oauth2(config)

    return redirect(url)
  else:
    return redirect("http://127.0.0.1:3000?nylasConnected=true")


@nylas_blueprint.route("/callback", methods=["GET"])
def authorized():
  if session.get("grant_id") is None:
    code = request.args.get("code")
    exchangeRequest = CodeExchangeRequest({
      "redirect_uri": "http://127.0.0.1:5000/nylas/callback",
      "code": code,
      "client_id": Config.NYLAS_CLIENT_ID
    })
    exchange = nylas.auth.exchange_code_for_token(exchangeRequest)
    session["grant_id"] = exchange.grant_id
    
    return redirect("http://127.0.0.1:3000?nylasConnected=true")


@nylas_blueprint.route("/recent-emails", methods=["GET"])
def recent_emails():
  query_params = {"limit": 20}

  try:
    messages, _, _ = nylas.messages.list(session["grant_id"], query_params)

    return jsonify(messages)
  except Exception as e:
    return f'{e}' 


@nylas_blueprint.route("/primary-calendar", methods=["GET"])
def primary_calendar():
  query_params = {"limit": 10}
  try:
    calendars, _, _ = nylas.calendars.list(session["grant_id"], query_params)

    for primary in calendars:
      if primary.is_primary is True:
        session["calendar"] = primary.id
        
      return redirect("http://127.0.0.1:5000/nylas/list-events")
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
@nylas_blueprint.route("/webhook", methods=["POST"])
def nylas_webhook():
    data = request.json  # Get the JSON data sent by Nylas

    # Check if the notification is for a new email
    if data["deltas"] and data["deltas"][0]["object"] == "message" and data["deltas"][0]["event"] == "create":
        message_id = data["deltas"][0]["id"]  # Get the message ID
        # Fetch the message details using Nylas API (assuming you've already handled authentication)
        message = nylas.messages.get(message_id)
        # Process the message as needed, e.g., log it, create a calendar event, etc.
        print(f"New email received: Subject: {message.subject}, From: {message.from_}")

    return jsonify(success=True), 200

