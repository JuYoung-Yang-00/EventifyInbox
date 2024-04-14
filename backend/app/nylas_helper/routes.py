from flask import Blueprint, request, redirect, session, jsonify, Response
from nylas import Client
from config import Config
from nylas.models.auth import URLForAuthenticationConfig
from nylas.models.auth import CodeExchangeRequest
import os
import hashlib
import hmac
from app.langchain_helper import langchain_helper

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
    expected_signature = hmac.new(webhook_secret.encode(), data, hashlib.sha256).hexdigest()
    is_valid = hmac.compare_digest(expected_signature, signature)
    return is_valid


@nylas_blueprint.route("/webhook", methods=['GET', 'POST'])
def nylas_webhook():
    if request.method == "GET":
        challenge = request.args.get("challenge")
        if challenge:
            return Response(challenge, mimetype='text/plain')

    webhook_secret = os.getenv('WEBHOOK_SECRET')
    signature = request.headers.get('X-Nylas-Signature')
    if not verify_nylas_signature(request.data, signature, webhook_secret):
        return "Signature verification failed!", 401
      
    #1. check if email is relevant to task and webhook is for email received
    #2. if relevant, send to langchain (llm)
    #3. if llm decides to create new calendar event, create new calendar event
    #4. Send email notification to user about newly created event
    data = request.get_json(silent=True)
    if data and is_relevant_to_task(data):
        decision, details = langchain_helper.get_response_from_llm(data)
        if decision == "yes" and details:
            event_response = create_event(details['grant_id'], session['calendar'], details['title'], details['start_time'], details['end_time'], details['description'])
            if event_response['status'] == 'success':
                email_response = send_notification_email(details['grant_id'], details['recipient_email'], "[EventifyInbox] New Calendar Event Created", f"A new calendar event has been created based on your recent email titled '{details['subject']}'. Please check your calendar for more details!")
                return jsonify(success=True, email_response=email_response), 200
            else:
                return jsonify(event_response), 500
    return "Invalid JSON data", 400


# Check if email is relevant to task and webhook is for email received
def is_relevant_to_task(email_data):
    keywords = ["task", "todo", "remind", "schedule", "meeting", "event", "appointment", "deadline", "reminder", "calendar", "plan", "agenda", "assignment", "due"]
    # Check if the email is not sent
    if 'SENT' not in email_data.get('folders', []):
        subject = email_data.get('subject', "").lower()
        body = email_data.get('body', "").lower()
        # Check if the subject or body contains task-related keywords
        return any(keyword in subject or keyword in body for keyword in keywords)
    return False
  
  
# Create event on the primary calendar based on llm's response
def create_event(grant_id, calendar_id, title, start_time, end_time, description):
    try:
        event = nylas.events.create(
            grant_id=grant_id,
            request_body={
                "title": title,
                "when": {
                    "start_time": start_time,
                    "end_time": end_time
                },
                "description": description
            },
            query_params={
                "calendar_id": calendar_id
            }
        )
        return {"status": "success", "message": "Event created successfully", "event": event}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
# Send an email notification to the user
def send_notification_email(grant_id, recipient_email, subject, description):
    email_body = {
        "to": [{"email": recipient_email}],
        "subject": subject,
        "body": description,
    }
    try:
        message = nylas.messages.send(grant_id, request_body=email_body)
        print("Notification email sent successfully!", message)
        return {"status": "success", "message": "Email sent successfully"}
    except Exception as e:
        print(f"Failed to send email: {e}")
        return {"status": "error", "message": str(e)}
