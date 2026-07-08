"""
Tool Rendering Weather Demo — Backend
======================================

AgentOS server with a get_weather backend tool for CopilotKit useRenderTool.

Run:
    .venvs/demo/bin/python test/backend/main.py

Endpoints:
    POST /agui              — AG-UI (CopilotKit)
    GET  /agents            — agent list (for db_id)
    GET  /sessions          — session list
    GET  /sessions/{id}/runs — chat history
"""

import os
from pathlib import Path

from agno.agent.agent import Agent
from agno.db.mysql import MySQLDb
from agno.models.dashscope import DashScope
from agno.os import AgentOS
from agno.os.interfaces.agui import AGUI
from agno.tools import tool

# Load .env from backend directory if present
_env_file = Path(__file__).parent / ".env"
if _env_file.exists():
    for line in _env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "ljw79618")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "agent_platform")

AI_MODEL_NAME = os.getenv("AI_MODEL_NAME", "qwen3-30b-a3b-instruct-2507")
AI_MODEL_API_URL = os.getenv(
    "AI_MODEL_API_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
)
AI_MODEL_API_KEY = os.getenv("AI_MODEL_API_KEY", "")

db_url = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
    f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"
)

db = MySQLDb(id="tool-rendering-mysql", db_url=db_url)

model = DashScope(
    id=AI_MODEL_NAME,
    api_key=AI_MODEL_API_KEY,
    base_url=AI_MODEL_API_URL,
)


@tool
def get_weather(location: str) -> dict:
    """Get detailed weather for a location. Returns structured data for frontend rendering."""
    data = {
        "San Francisco": {
            "city": "San Francisco",
            "temperature": 18,
            "humidity": 65,
            "wind_speed": 12,
            "conditions": "Sunny",
        },
        "New York": {
            "city": "New York",
            "temperature": 22,
            "humidity": 55,
            "wind_speed": 8,
            "conditions": "Cloudy",
        },
        "Tokyo": {
            "city": "Tokyo",
            "temperature": 26,
            "humidity": 70,
            "wind_speed": 5,
            "conditions": "Rainy",
        },
        "London": {
            "city": "London",
            "temperature": 15,
            "humidity": 80,
            "wind_speed": 15,
            "conditions": "Overcast",
        },
        "Paris": {
            "city": "Paris",
            "temperature": 20,
            "humidity": 60,
            "wind_speed": 10,
            "conditions": "Partly cloudy",
        },
    }
    return data.get(
        location,
        {
            "city": location,
            "temperature": 20,
            "humidity": 60,
            "wind_speed": 10,
            "conditions": "Partly cloudy",
        },
    )


weather_agent = Agent(
    id="weather-agent",
    name="Weather Agent",
    model=model,
    db=db,
    tools=[get_weather],
    add_history_to_context=True,
    num_history_runs=5,
    instructions="""You help users check weather. When asked about weather, always use the get_weather tool.

The tool returns structured data that the frontend will render as a weather card.
Keep your text replies brief after the tool runs.""",
    markdown=True,
)

agent_os = AgentOS(
    description="Tool Rendering weather demo for CopilotKit",
    agents=[weather_agent],
    db=db,
    interfaces=[AGUI(agent=weather_agent)],
    cors_allowed_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
)
app = agent_os.get_app()

if __name__ == "__main__":
    print("Tool Rendering Weather Backend")
    print(f"  Model:    {AI_MODEL_NAME}")
    print(f"  MySQL:    {MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}")
    print("  AG-UI:    http://localhost:8000/agui")
    print("  Sessions: http://localhost:8000/sessions?type=agent&component_id=weather-agent&db_id=<db_id>")
    agent_os.serve(app="main:app", host="0.0.0.0", port=8000, reload=True)
