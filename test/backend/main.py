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
    POST /components        — Studio: create agents/teams/workflows
    GET  /registry          — Studio: list models, tools, dbs
"""

import asyncio
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path

from agno.agent.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.models.dashscope import DashScope
from agno.os import AgentOS
from agno.os.config import AgentOSConfig
from agno.os.interfaces.agui import AGUI
from agno.registry import Registry
from agno.run import RunContext
from agno.tools import tool
from agno.tools.function import Function
from agno.vectordb.pgvector import PgVector, SearchType
from agno.workflow.types import StepInput, StepOutput

# Load .env from backend directory if present
_env_file = Path(__file__).parent / ".env"
if _env_file.exists():
    for line in _env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

DB_DIR = Path(__file__).parent / "tmp"
DB_DIR.mkdir(exist_ok=True)

AI_MODEL_NAME = os.getenv("AI_MODEL_NAME", "qwen3-30b-a3b-instruct-2507")
AI_MODEL_API_URL = os.getenv(
    "AI_MODEL_API_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
)
AI_MODEL_API_KEY = os.getenv("AI_MODEL_API_KEY", "")
# Comma-separated model ids exposed in Studio / Registry
AI_MODEL_IDS = [
    model_id.strip()
    for model_id in os.getenv(
        "AI_MODEL_IDS",
        "qwen3-30b-a3b-instruct-2507,qwen-plus,qwen-turbo,qwen-max",
    ).split(",")
    if model_id.strip()
]

PGVECTOR_URL = os.getenv("PGVECTOR_URL", "postgresql+psycopg://ai@localhost:5532/ai")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-v3")
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "1024"))

sqlite_file = os.getenv("SQLITE_DB_FILE", str(DB_DIR / "agent_platform.db"))
knowledge_contents_file = os.getenv(
    "KNOWLEDGE_SQLITE_FILE", str(DB_DIR / "knowledge_contents.db")
)

db = SqliteDb(id="weather-demo-db", db_file=sqlite_file)
contents_db = SqliteDb(id="knowledge-contents-db", db_file=knowledge_contents_file)

embedder = OpenAIEmbedder(
    id=EMBEDDING_MODEL,
    api_key=AI_MODEL_API_KEY,
    base_url=AI_MODEL_API_URL,
    dimensions=EMBEDDING_DIMENSIONS,
)

demo_knowledge = Knowledge(
    name="Demo Knowledge",
    description="Upload files from os.agno.com Knowledge page",
    vector_db=PgVector(
        db_url=PGVECTOR_URL,
        table_name="demo_knowledge_vectors",
        search_type=SearchType.hybrid,
        embedder=embedder,
    ),
    contents_db=contents_db,
)

def make_dashscope_model(model_id: str) -> DashScope:
    return DashScope(
        id=model_id,
        api_key=AI_MODEL_API_KEY,
        base_url=AI_MODEL_API_URL,
    )


models = [make_dashscope_model(model_id) for model_id in AI_MODEL_IDS]
default_model = next((m for m in models if m.id == AI_MODEL_NAME), models[0])


def _is_mock_enabled(dependencies: dict | None) -> bool:
    if not dependencies:
        return False
    mock = dependencies.get("mock", False)
    if isinstance(mock, str):
        return mock.lower() in ("true", "1", "yes")
    return bool(mock)


@tool
def get_weather(location: str, run_context: RunContext) -> dict:
    """Get detailed weather for a location. Returns structured data for frontend rendering."""
    dependencies = run_context.dependencies or {}
    mock = _is_mock_enabled(dependencies)

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
    result = data.get(
        location,
        {
            "city": location,
            "temperature": 20,
            "humidity": 60,
            "wind_speed": 10,
            "conditions": "Partly cloudy",
        },
    )

    if mock:
        result = {
            **result,
            "_mock": {
                "mock": True,
                "location_requested": location,
                "run_id": run_context.run_id,
                "session_id": run_context.session_id,
                "dependency_keys": sorted(dependencies.keys()),
            },
        }

    return result


# --- DB tool sync: fixed tools (code) + dynamic tools (console DB) ---
FIXED_TOOLS = [get_weather]
DB_TOOLS_FILE = DB_DIR / "db_tools.json"
TOOL_SYNC_INTERVAL = int(os.getenv("TOOL_SYNC_INTERVAL", "30"))


def read_db_tool_names() -> list[str]:
    """Read enabled tool names from console DB. Demo uses a JSON file."""
    if not DB_TOOLS_FILE.exists():
        return []
    data = json.loads(DB_TOOLS_FILE.read_text())
    return [name for name in data.get("tool_names", []) if name]


def sync_registry_tools(registry: Registry) -> list[str]:
    """Merge fixed tools with DB tools. Updates GET /registry and runtime rehydrate."""
    db_tools = []
    for name in read_db_tool_names():
        def _entrypoint(query: str, _name=name) -> str:
            return f"{_name}:{query}"

        _entrypoint.__name__ = name
        db_tools.append(Function(name=name, entrypoint=_entrypoint))

    registry.tools = list(FIXED_TOOLS) + db_tools
    registry.__dict__.pop("_entrypoint_lookup", None)
    return [t.name for t in registry.tools]


def transform_content(step_input: StepInput) -> StepOutput:
    """Studio Custom Executor demo: uppercase the previous step output."""
    text = step_input.previous_step_content or step_input.input or ""
    transformed = f"[TRANSFORMED] {str(text).upper()} [END]"
    return StepOutput(
        step_name="TransformContent",
        content=transformed,
        success=True,
    )


def is_tech_topic(step_input: StepInput) -> bool:
    """Studio Condition/Router demo: return True when input looks tech-related."""
    topic = step_input.input or step_input.previous_step_content or ""
    keywords = ("ai", "tech", "software", "code", "programming", "agent")
    return any(keyword in topic.lower() for keyword in keywords)


registry = Registry(
    name="Weather Demo Registry",
    models=models,
    tools=list(FIXED_TOOLS),
    functions=[transform_content, is_tech_topic],
    dbs=[db, contents_db],
    knowledge=[demo_knowledge],
)

weather_agent = Agent(
    id="weather-agent",
    name="Weather Agent",
    model=default_model,
    db=db,
    tools=[get_weather],
    add_history_to_context=True,
    num_history_runs=5,
    instructions="""You help users check weather and related assistant tasks.

When asked about weather, always use the get_weather tool.
The tool returns structured data that the frontend will render as a weather card.

When asked for a QR code, use the generate_qr tool if it is available in this run
(provided by CopilotKit MCP Apps via AG-UI client_tools). Pass the content in text.
Keep text replies brief after tools run.""",
    markdown=True,
)

knowledge_agent = Agent(
    id="knowledge-agent",
    name="Knowledge Agent",
    model=default_model,
    db=db,
    knowledge=demo_knowledge,
    search_knowledge=True,
    add_history_to_context=True,
    num_history_runs=5,
    instructions="""You answer questions using the attached knowledge base.
Search knowledge before answering. Cite the source when possible.""",
    markdown=True,
)


@asynccontextmanager
async def lifespan(app, agent_os):
    names = sync_registry_tools(agent_os.registry)
    print(f"Registry tools: {names}")

    async def _periodic_sync() -> None:
        while True:
            await asyncio.sleep(TOOL_SYNC_INTERVAL)
            try:
                names = sync_registry_tools(agent_os.registry)
                print(f"Registry tools re-synced: {names}")
            except Exception as exc:
                print(f"Tool sync failed: {exc}")

    task = asyncio.create_task(_periodic_sync())
    try:
        yield
    finally:
        task.cancel()


agent_os = AgentOS(
    description="Tool Rendering weather demo for CopilotKit",
    agents=[weather_agent, knowledge_agent],
    db=db,
    registry=registry,
    knowledge=[demo_knowledge],
    config=AgentOSConfig(available_models=AI_MODEL_IDS),
    interfaces=[AGUI(agent=weather_agent)],
    lifespan=lifespan,
    # Include os.agno.com so AgentOS Studio can reach this local instance.
    # Custom origins override AgentOS defaults, so list them explicitly.
    cors_allowed_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "https://os.agno.com",
        "https://os-stg.agno.com",
        "https://app.agno.com",
        "https://agno.com",
        "https://www.agno.com",
    ],
)
app = agent_os.get_app()

if __name__ == "__main__":
    print("Tool Rendering Weather Backend")
    print(f"  Default:  {default_model.id}")
    print(f"  Models:   {', '.join(AI_MODEL_IDS)}")
    print(f"  SQLite:   {sqlite_file}")
    print(f"  Contents: {knowledge_contents_file}")
    print(f"  PgVector: {PGVECTOR_URL}")
    print("  AG-UI:    http://localhost:8000/agui")
    print("  Knowledge: https://os.agno.com (sidebar -> Knowledge)")
    print("  Studio:   https://os.agno.com/studio/workflows/create")
    print("  Functions: transform_content, is_tech_topic")
    print(f"  DB tools:  {DB_TOOLS_FILE} (edit tool_names, sync every {TOOL_SYNC_INTERVAL}s)")
    print("  Sessions: http://localhost:8000/sessions?type=agent&component_id=weather-agent&db_id=<db_id>")
    agent_os.serve(app="main:app", host="0.0.0.0", port=8000, reload=True)
