from dotenv import load_dotenv
from fastapi import FastAPI
from fastmcp import FastMCP
from pydantic import BaseModel

from agent.orchestrator import AIAgent


class AskRequest(BaseModel):
    query: str


load_dotenv()

# Create FastMCP first
mcp = FastMCP(name="My First MCP Server")


@mcp.tool
def query_database(query: str) -> dict:
    """Run a database query"""
    return {"result": "data"}


# Build the MCP ASGI app
mcp_app = mcp.http_app(path="/mcp")

# Create FastAPI and pass MCP lifespan
app = FastAPI(lifespan=mcp_app.lifespan, title="AI Agent API")

# Mount MCP under FastAPI
app.mount("", mcp_app)

agent = AIAgent()


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/ask")
async def ask_ai(payload: AskRequest):
    return await agent.chat(payload.query)
