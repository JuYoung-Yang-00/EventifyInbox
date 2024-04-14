from flask import Blueprint, request, redirect, session, jsonify, Response
from nylas import Client
from config import Config
from nylas.models.auth import URLForAuthenticationConfig
from nylas.models.auth import CodeExchangeRequest

import os
import hashlib
import hmac
from app.langchain_helper import langchain_helper
from flask import current_app

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
    try:
        if session.get("grant_id") is None:
            code = request.args.get("code")
            exchangeRequest = CodeExchangeRequest({
                "redirect_uri": "https://api.eventifyinbox.com/nylas/callback",
                "code": code,
                "client_id": Config.NYLAS_CLIENT_ID
            })
            exchange = nylas.auth.exchange_code_for_token(exchangeRequest)
            session["grant_id"] = exchange.grant_id
            current_app.db.users.update_one(
                {'grant_id': session["grant_id"]},
                {'$set': {'grant_id': session["grant_id"]}},
                upsert=True
            )
    except Exception as e:
        current_app.logger.error(f"An error occurred during authentication: {str(e)}")
        return "An Internal Error Occurred", 500

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
        # Save primary calendar ID in MongoDB for the user's grant_id
        current_app.db.users.update_one(
            {'grant_id': session["grant_id"]},
            {'$set': {'primary_calendar_id': primary.id}},
            upsert=True
        )
        
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
    print(f"Data: {data}")
    print(f"Received Signature: {signature}")
    print(f"Expected Signature: {expected_signature}")
    print(f"Signature Valid: {is_valid}")
    return is_valid
  
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
    if not verify_nylas_signature(request.data, signature, webhook_secret):
        print("Signature verification failed.")
        return "Signature verification failed!", 401

    data = request.get_json(silent=True)
    if data:
      print(f"Webhook data received: {data}")
      email_data = data.get('data', {}).get('object', {})
      if is_relevant_to_task(email_data):
        decision, details = langchain_helper.get_response_from_llm(data)
        if decision == "yes":
            event_response = create_event(details['grant_id'], details['title'], details['start_time'], details['end_time'], details['description'])
            # if event_response[0] == 'success':
            email_response = send_notification_email(details['recipient_email'], "[EventifyInbox] New Calendar Event Created", f"A new calendar event has been created based on your recent email regarding '{details['description']}'. Please check your calendar for more details!")
            print("Event created and notification email sent!!")
            return jsonify(success=True, event_response=event_response, email_response=email_response), 200
            # else:
            #   return "Event creation failed", 200
          # else:
          #     return "No details provided for event creation", 200
        else:
          return "Decision was no", 200
      else:
        return "Not relevant to task", 200

# Function to check if email is relevant to task and webhook is for email received
def is_relevant_to_task(email_data):
    keywords = ["task", "todo", "remind", "schedule", "meeting", "event", "appointment", "deadline", "reminder", "calendar", "plan", "agenda", "assignment", "due"]
    folders = email_data.get('folders', [])
    print(f"Email folders: {folders}")

    if 'SENT' in folders:
        print("Email is sent, not received. Ignoring.")
        return False

    subject = email_data.get('subject', "").lower()
    body = email_data.get('body', "").lower()
    if any(keyword in subject or keyword in body for keyword in keywords):
        print("Email contains relevant keywords and is considered for further processing.")
        return True

    print("Email does not contain relevant keywords.")
    return False

# @nylas_blueprint.route("/webhook", methods=['GET', 'POST'])
# def nylas_webhook():
#     if request.method == "GET":
#         challenge = request.args.get("challenge")
#         if challenge:
#             return Response(challenge, mimetype='text/plain')

#     webhook_secret = os.getenv('WEBHOOK_SECRET')
#     if not webhook_secret:
#         print("Webhook secret not configured.")
#         return "Webhook secret not configured.", 500

#     signature = request.headers.get('X-Nylas-Signature')
#     if not verify_nylas_signature(request.data, signature, webhook_secret):
#         print( f'printing webhook_secre: {webhook_secret}')
#         print("Signature verification failed.")
#         return "Signature verification failed!", 401

#     data = request.get_json(silent=True)
#     if data:
#       print(f'THIS IS THE WEBHOOK DATA FROM HERE: {data} TO HERE')
#       if is_relevant_to_task:
#         decision, details = langchain_helper.get_response_from_llm(data)
#         if decision == "yes" :
#           if details:
#             event_response = create_event(details['grant_id'], details['title'], details['start_time'], details['end_time'], details['description'])
#             if event_response['status'] == 'success':
#               email_response = send_notification_email(details['recipient_email'], "[EventifyInbox] New Calendar Event Created", f"A new calendar event has been created based on your recent email titled '{details['subject']}'. Please check your calendar for more details!")
#               return jsonify(success=True, email_response=email_response), 200
#             else:
#               return "Event creation failed", 200
#           else:
#               return "No details", 200
#         else:
#           return "Decision was no", 200
#       else:
#         return "Not relevant to task", 200


# # Check if email is relevant to task and webhook is for email received
# def is_relevant_to_task(email_data):
#     keywords = ["task", "todo", "remind", "schedule", "meeting", "event", "appointment", "deadline", "reminder", "calendar", "plan", "agenda", "assignment", "due"]
#     # Check if the email is marked as sent
#     if 'SENT' in email_data.get('folders', []):
#         print("Email is sent, not received. Ignoring.")
#         return False
#     subject = email_data.get('subject', "").lower()
#     body = email_data.get('body', "").lower()
#     # Check if the subject or body contains task-related keywords
#     if any(keyword in subject or keyword in body for keyword in keywords):
#         print("Email contains relevant keywords and is considered for further processing.")
#         return True

#     print("Email does not contain relevant keywords.")
#     return False

  
  
# Create event on the primary calendar based on llm's response
def create_event(grant_id, title, start_time, end_time, description):
    user = current_app.db.users.find_one({'grant_id': grant_id})
    if not user or 'primary_calendar_id' not in user:
        print(f"No primary calendar found for grant_id: {grant_id}")
        return jsonify({"status": "error", "message": "No primary calendar found"}), 404

    calendar_id = user['primary_calendar_id']
    try:
        # Set up the request body for creating the event
        request_body = {
            "title": title,
            "when": {
                "start_time": int(start_time),
                "end_time": int(end_time)
            },
            "description": description
        }
        # Prepare the query parameters, if any
        query_params = {
            "calendar_id": calendar_id
        }
        event = nylas.events.create(grant_id, request_body=request_body, query_params=query_params)
        return {"status": "success", "message": "Event created successfully", "event": event}, 200
    except Exception as e:
        print(f"Failed to create event: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

      
    
# Send an email notification to the user
# sender_email = os.getenv('EMAIL')
def send_notification_email(recipient_email, subject, description):
    grant_id = os.getenv("NYLAS_GRANT_ID") 
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