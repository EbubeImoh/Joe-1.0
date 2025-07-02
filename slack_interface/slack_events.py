# Import necessary modules from FastAPI for creating API endpoints and handling requests.
from fastapi import APIRouter, Request, Header, HTTPException
# Import modules for cryptographic operations (HMAC, SHA256), OS environment variables, and time.
import hmac, hashlib, os, time
# Import WebClient from slack_sdk for interacting with the Slack API.
from slack_sdk import WebClient
# Import the orchestrator instance from orchestrator/instance.py
from orchestrator.instance import orchestrator
import logging

# ===== Environment Setup =====
# Create an APIRouter instance to define API routes for Slack events.
router = APIRouter()

# ===== Slack API Setup =====
# Retrieve the Slack signing secret from ===nvironment variables. This is used to verify requests from Slack.
SLACK_SIGNING_SECRET = os.getenv("SLACK_S=IGNING_SECRET")
# Retrieve the Slack bot token from environment variables. This is used to authenticate API calls to Slack.
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
# Initialize the Slack WebClient with the bot token.
slack_client = WebClient(token=SLACK_BOT_TOKEN)

# The 'orchestrator' instance is now imported from orchestrator/instance.py
# Ensure that orchestrator/instance.py initializes it correctly with all necessary agents and API keys.

# ===== Slack Events API Setup =====
# Asynchronous function to verify the signature of incoming requests from Slack.
async def verify_slack_signature(request: Request, x_slack_signature: str, x_slack_request_timestamp: str):
    """
    Verifies the signature of an incoming Slack request to ensure it's genuine.

    Args:
        request: The incoming FastAPI Request object.
        x_slack_signature: The signature provided by Slack in the 'X-Slack-Signature' header.
        x_slack_request_timestamp: The timestamp provided by Slack in the 'X-Slack-Request-Timestamp' header.

    Raises:
        HTTPException: If the timestamp is invalid or the signature does not match.
    """
    # Check if the request timestamp is older than 5 minutes. If so, it might be a replay attack.
    if abs(time.time() - int(x_slack_request_timestamp)) > 60 * 5:
        raise HTTPException(status_code=400, detail="Invalid timestamp")
    # Get the raw request body.
    body = await request.body()
    # Create the basestring by concatenating the version number, timestamp, and request body.
    basestring = f"v0:{x_slack_request_timestamp}:{body.decode()}"
    # Hash the basestring using HMAC-SHA256 with the Slack signing secret.
    my_signature = "v0=" + hmac.new(
        SLACK_SIGNING_SECRET.encode(), basestring.encode(), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(my_signature, x_slack_signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

# Define a POST endpoint to receive events from Slack.
@router.post("/slack/events")
async def slack_events(
    request: Request,
    # Extract the 'X-Slack-Signature' header from the request.
    x_slack_signature: str = Header(None),
    # Extract the 'X-Slack-Request-Timestamp' header from the request.
    x_slack_request_timestamp: str = Header(None)
):
    """
    Handles incoming events from Slack, such as messages, reactions, etc.
    This endpoint first verifies the request signature and then processes the event.
    It also handles Slack's URL verification challenge during setup.
    """
    try:
        await verify_slack_signature(request, x_slack_signature, x_slack_request_timestamp)
        payload = await request.json()
        # Handle Slack's URL verification challenge.
        # When setting up the Events API endpoint in Slack, Slack sends a challenge request.
        # The app must respond with the 'challenge' value from the payload.
        if payload.get("type") == "url_verification":
            return {"challenge": payload["challenge"]}

        # Extract the actual event data from the payload.
        event = payload.get("event", {})
        event_type = event.get("type")

        # Route events to their handlers
        if event_type == "message":
            # Prevent bot from responding to its own messages
            bot_user_id = os.getenv("BOT_USER_ID")
            if event.get("user") and (not bot_user_id or event.get("user") != bot_user_id):
                await handle_message_event(event)
        elif event_type == "reaction_added":
            await handle_reaction_event(event)
        # Add more event types as needed

        # Acknowledge the event receipt with an "ok" response.
        return {"ok": True}
    except Exception as e:
        logging.exception(f"Error in slack_events: {e}")
        # Always return 200 to Slack to avoid retries, but include error info
        return {"ok": False, "error": str(e)}

# Asynchronous function to handle 'message' events from Slack.
async def handle_message_event(event):
    """
    Handles incoming message events from Slack. This function is the ONLY place where
    user-facing Slack responses (chat_postMessage) should be sent for message events.
    Agents and the orchestrator MUST NOT call chat_postMessage directly—responses must
    always be routed through this handler to guarantee only one response per event.

    Args:
        event: The event data from Slack, containing information about the message and the user.
    """
    user = event.get("user")
    text = event.get("text", "")
    channel = event.get("channel")
    # Prevent bot from responding to its own messages
    bot_user_id = os.getenv("BOT_USER_ID")
    if user is None or (bot_user_id and user == bot_user_id):
        return
    response_sent = False
    try:
        # Use the Orchestrator's classify_task static method
        task = await orchestrator.classify_task(text=text, user=user, channel=channel)
        result = await orchestrator.route_task(task)
        # Send result back to Slack
        response_text = result.get("report") or str(result)
        slack_client.chat_postMessage(channel=channel, text=response_text)
        response_sent = True
    except Exception as e:
        logging.exception(f"Error in handle_message_event: {e}")
        if not response_sent:
            try:
                slack_client.chat_postMessage(channel=channel, text=f"Sorry, an error occurred: {e}")
            except Exception:
                pass

# Asynchronous function to handle 'reaction_added' events from Slack.
async def handle_reaction_event(event):
    """Processes incoming reaction events from Slack."""
    channel = event.get("item", {}).get("channel")
    timestamp = event.get("item", {}).get("ts")
    reaction = event.get("reaction")
    # Add the reaction to the message using the Slack WebClient.
    if reaction and channel and timestamp:
        # Use the reactions_add method to add the reaction to the specified message.
        # This requires the channel ID, message timestamp, and the reaction name.
        slack_client.reactions_add(channel=channel, timestamp=timestamp, name=reaction)


# Function to notify a user in Slack, either as a direct message or in a channel.
async def send_notification(channel, text):
    """
    Sends explicit notifications to users or channels. This should NOT be used for normal
    responses to Slack events—only for out-of-band notifications (e.g., reminders, alerts).

    Args:
        channel: The channel or user ID to send the notification to.
        text: The text of the notification message.
    """
    slack_client.chat_postMessage(channel=channel, text=text)