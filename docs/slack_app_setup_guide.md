# Slack App Setup Guide for Zia-AI

This guide will help you register, configure, and install the Slack app required for Zia-AI to interact with your Slack workspace.

---

## 1. Create a New Slack App

1. Go to the [Slack API: Your Apps](https://api.slack.com/apps) page.
2. Click **"Create New App"**.
3. Choose **"From scratch"**.
4. Enter an app name (e.g., `Zia-AI`) and select your workspace.
5. Click **"Create App"**.

---

## 2. Configure OAuth & Permissions

1. In your app settings, go to **OAuth & Permissions**.
2. Under **Scopes**, add the following **Bot Token Scopes** (minimum required):
    - `app_mentions:read`
    - `channels:history`
    - `channels:read`
    - `chat:write`
    - `commands`
    - `groups:history`
    - `groups:read`
    - `im:history`
    - `im:read`
    - `im:write`
    - `mpim:history`
    - `mpim:read`
    - `reactions:write`
    - `users:read`
3. If your app will use interactive components (buttons, dropdowns), also add:
    - `interactivity`
4. Click **Save Changes**.

---

## 3. Set Up Event Subscriptions

1. Go to **Event Subscriptions** in the sidebar.
2. Toggle **Enable Events** to **On**.
3. Set the **Request URL** to your server’s public endpoint (e.g., `https://yourdomain.com/slack/events`).  
   > For local development, use [ngrok](https://ngrok.com/) to expose your local server.
4. Under **Subscribe to Bot Events**, add:
    - `app_mention`
    - `message.im`
    - `message.channels`
    - `reaction_added`
    - `reaction_removed`
5. Click **Save Changes**.

---

## 4. Add Slash Commands (Optional)

1. Go to **Slash Commands** in the sidebar.
2. Click **Create New Command**.
3. Fill in:
    - **Command:** `/zia` (or your preferred command)
    - **Request URL:** Your server endpoint (e.g., `https://yourdomain.com/slack/commands`)
    - **Short Description:** (e.g., "Interact with Zia-AI")
    - **Usage Hint:** (e.g., `[your question or command]`)
4. Click **Save**.

---

## 5. Install the App to Your Workspace

1. Go to **OAuth & Permissions**.
2. Click **Install App to Workspace**.
3. Authorize the required permissions.

---

## 6. Retrieve and Configure Credentials

1. In **OAuth & Permissions**, copy the **Bot User OAuth Token** (starts with `xoxb-`).
2. In **Basic Information**, copy the **Signing Secret**.
3. Add these values to your `.env` file:
    ```
    SLACK_BOT_TOKEN=xoxb-...
    SLACK_SIGNING_SECRET=...
    ```
4. If using slash commands or interactive components, ensure your endpoints are accessible and configured.

---

## 7. (Optional) Enable Interactivity

1. Go to **Interactivity & Shortcuts**.
2. Toggle **Interactivity** to **On**.
3. Set the **Request URL** to your server endpoint for interactive events (e.g., `https://yourdomain.com/slack/interactive`).

---

## 8. Test Your App

1. Start your backend server.
2. Send a direct message or mention the app in a channel.
3. Use your slash command (if configured).
4. Check for responses and Slack reactions.

---

## 9. Troubleshooting

- If events are not received, check your endpoint URL and server logs.
- Ensure your app is invited to the relevant channels.
- Use Slack’s **Event Logs** and **API Tester** for debugging.

---

## References

- [Slack API Documentation](https://api.slack.com/)
- [ngrok (for local development)](https://ngrok.com/)

---

**End of Slack App Setup Guide**