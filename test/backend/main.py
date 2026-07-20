"""
Tool Rendering Weather Demo — Backend
======================================

AgentOS server with a get_weather backend tool for CopilotKit useRenderTool,
plus a multi-agent article workflow (Condition + Function).

Run:
    .venvs/demo/bin/python test/backend/main.py

Endpoints:
    POST /agui              — AG-UI (CopilotKit)
    GET  /agents            — agent list (for db_id)
    GET  /workflows         — workflow list (article-workflow)
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
from textwrap import dedent

from agno.agent.agent import Agent
from agno.db.postgres import PostgresDb
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
from agno.workflow.condition import Condition
from agno.workflow.step import Step
from agno.workflow.types import StepInput, StepOutput
from agno.workflow.workflow import Workflow

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

# Shared Postgres (agent-platform-postgres / pgvector). Override via .env.
PGVECTOR_URL = os.getenv(
    "PGVECTOR_URL", "postgresql+psycopg://ai:ai@localhost:5432/ai"
)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-v3")
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "1024"))

sqlite_file = os.getenv("SQLITE_DB_FILE", str(DB_DIR / "agent_platform.db"))

# Sessions stay on SQLite; knowledge contents + vectors share the existing Postgres.
db = SqliteDb(id="weather-demo-db", db_file=sqlite_file)
contents_db = PostgresDb(
    id="knowledge-contents-db",
    db_url=PGVECTOR_URL,
    knowledge_table="demo_knowledge_contents",
)
contents_db_1 = PostgresDb(
    id="knowledge-contents-db-1",
    db_url=PGVECTOR_URL,
    knowledge_table="demo_knowledge1_contents",
)

embedder = OpenAIEmbedder(
    id=EMBEDDING_MODEL,
    api_key=AI_MODEL_API_KEY,
    base_url=AI_MODEL_API_URL,
    dimensions=EMBEDDING_DIMENSIONS,
)

demo_knowledge = Knowledge(
    name="Demo Knowledge",
    description="Demo knowledge base backed by existing Postgres + pgvector",
    vector_db=PgVector(
        db_url=PGVECTOR_URL,
        table_name="demo_knowledge_vectors",
        search_type=SearchType.hybrid,
        embedder=embedder,
    ),
    contents_db=contents_db,
)

demo_knowledge1 = Knowledge(
    name="Demo Knowledge 1",
    description="Second demo knowledge base backed by existing Postgres + pgvector",
    vector_db=PgVector(
        db_url=PGVECTOR_URL,
        table_name="demo_knowledge1_vectors",
        search_type=SearchType.hybrid,
        embedder=embedder,
    ),
    contents_db=contents_db_1,
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


def format_article(step_input: StepInput) -> StepOutput:
    """Workflow function step: normalize writer output before the editor."""
    topic = step_input.input or "untitled"
    body = step_input.previous_step_content or ""
    formatted = (
        f"# Article Draft\n\n"
        f"**Topic:** {topic}\n\n"
        f"---\n\n"
        f"{body}\n\n"
        f"---\n"
        f"_Formatted by format_article function step._"
    )
    return StepOutput(
        step_name="FormatArticle",
        content=formatted,
        success=True,
    )


registry = Registry(
    name="Weather Demo Registry",
    models=models,
    tools=list(FIXED_TOOLS),
    functions=[transform_content, is_tech_topic, format_article],
    dbs=[db, contents_db, contents_db_1],
    knowledge=[demo_knowledge, demo_knowledge1],
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

# --- Multi-agent workflow: Condition + Function ---
topic_researcher = Agent(
    id="topic-researcher",
    name="Topic Researcher",
    model=default_model,
    instructions=(
        "Research the given topic and return 3-5 key findings. "
        "Be concise and factual. Do not write a full article."
    ),
    markdown=True,
)

tech_writer = Agent(
    id="tech-writer",
    name="Tech Writer",
    model=default_model,
    instructions=(
        "You write technical articles for engineers. "
        "Use the research findings to draft a clear, structured article "
        "with headings, bullet points, and practical takeaways."
    ),
    markdown=True,
)

general_writer = Agent(
    id="general-writer",
    name="General Writer",
    model=default_model,
    instructions=(
        "You write accessible articles for a general audience. "
        "Use the research findings to draft a friendly, easy-to-read article "
        "with a short intro, main points, and a conclusion."
    ),
    markdown=True,
)

content_editor = Agent(
    id="content-editor",
    name="Content Editor",
    model=default_model,
    instructions=(
        "You are an editor. Polish the formatted draft for clarity and flow. "
        "Keep the structure, fix awkward phrasing, and return the final article."
    ),
    markdown=True,
)

research_step = Step(
    name="research",
    description="Research the topic",
    agent=topic_researcher,
)

tech_write_step = Step(
    name="tech_write",
    description="Write a technical article from research",
    agent=tech_writer,
)

general_write_step = Step(
    name="general_write",
    description="Write a general-audience article from research",
    agent=general_writer,
)

format_step = Step(
    name="format_article",
    description="Normalize the draft with a custom function",
    executor=format_article,
)

edit_step = Step(
    name="edit",
    description="Polish the formatted draft",
    agent=content_editor,
)

article_workflow = Workflow(
    id="article-workflow",
    name="Article Workflow",
    description=(
        "Multi-agent article pipeline: Research -> Condition(tech/general write) "
        "-> Function(format) -> Edit. Same session keeps recent run history for steps."
    ),
    db=db,
    add_workflow_history_to_steps=True,
    num_history_runs=3,
    steps=[
        research_step,
        Condition(
            name="writer_route",
            description="Route to tech or general writer based on topic keywords",
            evaluator=is_tech_topic,
            steps=[tech_write_step],
            else_steps=[general_write_step],
        ),
        format_step,
        edit_step,
    ],
)


def seed_demo_knowledge() -> None:
    """Insert a small FAQ so search_knowledge has something to retrieve."""
    demo_knowledge.insert(
        name="Demo FAQ",
        text_content=dedent("""
            What is this demo?
            This AgentOS backend exposes a weather agent and a knowledge agent.

            How does knowledge search work?
            The knowledge-agent uses Agentic RAG (search_knowledge=True) to call
            search_knowledge_base against Demo Knowledge in Postgres + pgvector.

            How do I upload more documents?
            Use the AgentOS Knowledge UI at https://os.agno.com (sidebar -> Knowledge)
            or call the knowledge insert APIs on this server.
        """).strip(),
        skip_if_exists=True,
    )
    demo_knowledge1.insert(
        name="Demo Knowledge 1 FAQ",
        text_content=dedent("""
            What is Demo Knowledge 1?
            A second knowledge base registered alongside Demo Knowledge for multi-KB demos.

            When should I use Demo Knowledge 1?
            Use it to test selecting a different knowledge base in Studio / Registry.
        """).strip(),
        skip_if_exists=True,
    )


@asynccontextmanager
async def lifespan(app, agent_os):
    names = sync_registry_tools(agent_os.registry)
    print(f"Registry tools: {names}")

    try:
        await asyncio.to_thread(seed_demo_knowledge)
        print("Knowledge seeded: Demo FAQ (skip_if_exists)")
    except Exception as exc:
        print(f"Knowledge seed failed: {exc}")

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
    workflows=[article_workflow],
    db=db,
    registry=registry,
    knowledge=[demo_knowledge, demo_knowledge1],
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
    print("  Contents: Postgres tables demo_knowledge_contents, demo_knowledge1_contents")
    print(f"  PgVector: {PGVECTOR_URL}")
    print("  AG-UI:    http://localhost:8000/agui")
    print("  Knowledge: Demo Knowledge, Demo Knowledge 1")
    print("  Knowledge agent: knowledge-agent")
    print("  Knowledge UI: https://os.agno.com (sidebar -> Knowledge)")
    print("  Studio:   https://os.agno.com/studio/workflows/create")
    print("  Workflow: article-workflow (Research -> Condition -> Function -> Edit)")
    print("  Functions: transform_content, is_tech_topic, format_article")
    print(f"  DB tools:  {DB_TOOLS_FILE} (edit tool_names, sync every {TOOL_SYNC_INTERVAL}s)")
    print("  Sessions: http://localhost:8000/sessions?type=agent&component_id=weather-agent&db_id=<db_id>")
    agent_os.serve(app="main:app", host="0.0.0.0", port=8000, reload=True)
