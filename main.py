from fastapi import FastAPI, Request
from slack_interface.slack_events import router as slack_router
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# FastAPI application setup
app = FastAPI()
app.include_router(slack_router)

# Define a simple route
@app.get("/")
async def root():
    return {"message": "Zia-AI backend is running"}

# Define a route to handle Slack slash commands
@app.post("/slack/commands")
async def slack_commands(request: Request):
    data = await request.form()
    return {"response_type": "ephemeral", "text": "Slash command received!"}


# Import orchestrator instance
from orchestrator.instance import orchestrator

# ===== Importing Agents and Orchestrator =====
# (Moved to orchestrator/instance.py)