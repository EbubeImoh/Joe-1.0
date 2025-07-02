# Slack Interface Agent Setup Guide

This document details the steps to implement the Slack Interface Agent for Zia-AI, enabling robust Slack integration via the Events API, message and reaction handling, interactive components, and user notifications.

---

## 1. Implement Slack Event Listener (Events API)

- **Purpose:**  
  Receive and process events from Slack (e.g., messages, reactions, app mentions).

- **Steps:**
  1. **Expose an endpoint** (e.g., `/slack/events`) in your FastAPI app to receive POST requests from Slack.
  2. **Verify Slack requests** using the signing secret to ensure authenticity.
  3. **Handle Slack URL verification** by responding with the `challenge` parameter during initial setup.
  4. **Parse incoming events** and route them to the appropriate handler.

  **Example:**
  ````python
  # filepath: slack_interface/slack_events.py
  from fastapi import APIRouter, Request, Header, HTTPException
  import hmac, hashlib, os, time
  from slack_sdk import WebClient

  router = APIRouter()

  SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
  SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
  slack_client = WebClient(token=SLACK_BOT_TOKEN)

  def verify_slack_signature(request: Request, x_slack_signature: str, x_slack_request_timestamp: str):
      if abs(time.time() - int(x_slack_request_timestamp)) > 60 * 5:
          raise HTTPException(status_code=400, detail="Invalid timestamp")
      body = await request.body()
      basestring = f"v0:{x_slack_request_timestamp}:{body.decode()}"
      my_signature = "v0=" + hmac.new(
          SLACK_SIGNING_SECRET.encode(), basestring.encode(), hashlib.sha256
      ).hexdigest()
      if not hmac.compare_digest(my_signature, x_slack_signature):
          raise HTTPException(status_code=400, detail="Invalid signature")

  @router.post("/slack/events")
  async def slack_events(
      request: Request,
      x_slack_signature: str = Header(None),
      x_slack_request_timestamp: str = Header(None)
  ):
      # verify_slack_signature(request, x_slack_signature, x_slack_request_timestamp)
      payload = await request.json()
      # URL verification challenge
      if payload.get("type") == "url_verification":
          return {"challenge": payload["challenge"]}
      # Route event to handler
      event = payload.get("event", {})
      # ... call message/reaction/interactive handlers here ...
      return {"ok": True}

  async def handle_message_event(event):
      user = event.get("user")
      text = event.get("text", "")
      channel = event.get("channel")
      if event.get("channel_type") == "im" or "<@YOUR_BOT_USER_ID>" in text:
          # Process the message and generate a response
          response_text = "Hello! How can I assist you?"
          slack_client.chat_postMessage(channel=channel, text=response_text)
  ````

## 2. Implement Message Handler for DMs and Mentions

- **Purpose:**  
  Respond to direct messages and @mentions in channels.

- **Steps:**

  - Detect message events with `event["type"] == "message"`.
  - Check if the message is a DM or contains a mention of the bot.
  - Parse the message text and trigger the appropriate agent or workflow.
  - Send a response using the Slack Web API (`chat.postMessage`).

  **Example:**
  ````python
  # filepath: slack_interface/slack_events.py
  from slack_sdk import WebClient

  SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
  slack_client = WebClient(token=SLACK_BOT_TOKEN)

  async def handle_message_event(event):
      user = event.get("user")
      text = event.get("text", "")
      channel = event.get("channel")
      if event.get("channel_type") == "im" or "<@YOUR_BOT_USER_ID>" in text:
          # Process the message and generate a response
          response_text = "Hello! How can I assist you?"
          slack_client.chat_postMessage(channel=channel, text=response_text)
  ````

## 3. Implement Slack Reaction Handler

- **Purpose:**  
  Respond to emoji reactions added or removed from messages (e.g., for feedback or progress).

- **Steps:**

  - Listen for `reaction_added` and `reaction_removed` events.
  - Identify the message and user involved.
  - Trigger logic based on the reaction (e.g., mark task as complete, escalate, etc.).

  **Example:**
  ````python
  # filepath: slack_interface/slack_events.py
  from slack_sdk import WebClient

  SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
  slack_client = WebClient(token=SLACK_BOT_TOKEN)

  async def handle_reaction_event(event):
      reaction = event.get("reaction")
      user = event.get("user")
      item = event.get("item", {})
      # Implement custom logic based on reaction
      if reaction == "eyes":
          # e.g., log that someone is watching this task
          pass
  ````

## 4. Implement Interactive Components Handler

- **Purpose:**  
  Manage interactions with buttons, menus, and other interactive Slack components.

- **Steps:**

  - Listen for `block_actions` events.
  - Extract the action data and user information.
  - Perform the desired action (e.g., update a message, trigger a workflow).

  **Example:**
  ````python
  # filepath: slack_interface/slack_events.py
  from slack_sdk import WebClient

  SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
  slack_client = WebClient(token=SLACK_BOT_TOKEN)

  async def handle_interactive_component_event(event):
      actions = event.get("actions", [])
      for action in actions:
          # Handle different action types (e.g., button clicks, menu selections)
          pass
  ````

## 5. Implement User Notification System

- **Purpose:**  
  Notify users about important events, reminders, or updates from Zia-AI.

- **Steps:**

  - Decide on the notification triggers (e.g., scheduled times, event-based).
  - Format the notification message.
  - Send the notification using the Slack Web API (`chat.postMessage`).

  **Example:**
  ````python
  # filepath: slack_interface/slack_events.py
  from slack_sdk import WebClient

  SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
  slack_client = WebClient(token=SLACK_BOT_TOKEN)

  async def send_notification(channel, text):
      slack_client.chat_postMessage(channel=channel, text=text)
  ````

---

## Notes

- Replace `<@YOUR_BOT_USER_ID>` with your actual bot user ID in the code examples.
- Ensure all environment variables (e.g., `SLACK_SIGNING_SECRET`, `SLACK_BOT_TOKEN`) are correctly set in your deployment environment.
- This guide provides a foundational setup. Depending on your use case, you may need to implement additional logic, error handling, and security measures.

