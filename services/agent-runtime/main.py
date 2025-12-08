"""
Agent Runtime - FastAPI service for LangGraph agent execution.

Endpoints:
- POST /api/agents/run - Execute agent
- GET /api/agents/{agent_id}/runs - List agent runs
- GET /api/health - Health check
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging
import os
from datetime import datetime

# Import agents
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from langgraph_agents.agents.research_agent import ResearchAgent
from langgraph_agents.agents.expense_classifier import ExpenseClassifierAgent
from safety.prompt_injection_detector import PromptInjectionDetector
from safety.rate_limiter import RateLimiter
from langfuse.integrations.litellm import LiteLLMLangfuseTracer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Agent Runtime API",
    description="Multi-agent orchestration with LangGraph",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize safety harnesses
injection_detector = PromptInjectionDetector()
rate_limiter = RateLimiter()

# Initialize Langfuse tracer
langfuse_tracer = LiteLLMLangfuseTracer(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY", ""),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY", ""),
    host=os.getenv("LANGFUSE_HOST", "http://localhost:3000")
)

# Initialize agents
agent_config = {
    "qdrant_url": os.getenv("QDRANT_URL", "http://qdrant:6333"),
    "supabase_url": os.getenv("SUPABASE_URL"),
    "supabase_key": os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
    "odoo_url": os.getenv("ODOO_URL"),
    "odoo_db": os.getenv("ODOO_DB"),
    "odoo_username": os.getenv("ODOO_USERNAME"),
    "odoo_password": os.getenv("ODOO_PASSWORD"),
    "confidence_threshold": 0.7,
    "max_retries": 2,
    "ocr_confidence_threshold": 0.6
}

# Agent registry (lazy initialization)
agents = {}


# Pydantic models
class AgentRunRequest(BaseModel):
    """Request model for agent execution."""
    agent_id: str = Field(..., description="Agent identifier (research, expense, finance)")
    query: Optional[str] = Field(None, description="User query (for research agent)")
    receipt_url: Optional[str] = Field(None, description="Receipt URL (for expense classifier)")
    user_id: str = Field(..., description="User identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class AgentRunResponse(BaseModel):
    """Response model for agent execution."""
    run_id: str
    agent_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    trace_url: Optional[str] = None
    created_at: datetime


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    agents: List[str]
    services: Dict[str, str]


# Dependency: Check rate limit
async def check_rate_limit_dependency(user_id: str):
    """Check rate limit before processing request."""
    result = await rate_limiter.check_rate_limit(user_id)
    if not result["allowed"]:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limit_exceeded",
                "reason": result["reason"],
                "retry_after_seconds": result.get("retry_after_seconds", 60)
            }
        )
    return result


# Dependency: Check injection
def check_injection_dependency(query: Optional[str]):
    """Check for prompt injection attempts."""
    if not query:
        return

    detection = injection_detector.detect(query)
    if injection_detector.should_block(detection):
        logger.warning(f"Blocked injection attempt: {detection}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "prompt_injection_detected",
                "threat_level": detection["threat_level"].value,
                "patterns": [p["name"] for p in detection["matched_patterns"]]
            }
        )


# Endpoints
@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        agents=["research", "expense", "finance"],
        services={
            "qdrant": "connected" if os.getenv("QDRANT_URL") else "not_configured",
            "supabase": "connected" if os.getenv("SUPABASE_URL") else "not_configured",
            "langfuse": "connected" if os.getenv("LANGFUSE_PUBLIC_KEY") else "not_configured"
        }
    )


@app.post("/api/agents/run", response_model=AgentRunResponse)
async def run_agent(
    request: AgentRunRequest,
    background_tasks: BackgroundTasks,
    rate_limit_result: Dict = Depends(lambda: check_rate_limit_dependency(request.user_id)),
    injection_check: None = Depends(lambda: check_injection_dependency(request.query))
):
    """
    Execute an agent.

    Args:
        request: Agent run request

    Returns:
        Agent run response with results
    """
    logger.info(f"Running agent: {request.agent_id} for user: {request.user_id}")

    # Generate run ID
    import uuid
    run_id = str(uuid.uuid4())

    try:
        # Get or initialize agent
        if request.agent_id == "research":
            if "research" not in agents:
                from langchain.chat_models import ChatOpenAI
                llm = ChatOpenAI(model="gpt-4", temperature=0.7)
                agents["research"] = ResearchAgent(llm, agent_config)

            if not request.query:
                raise HTTPException(status_code=400, detail="query required for research agent")

            # Execute agent
            result = await agents["research"].run(
                query=request.query,
                user_id=request.user_id
            )

        elif request.agent_id == "expense":
            if "expense" not in agents:
                from langchain.chat_models import ChatOpenAI
                llm = ChatOpenAI(model="gpt-4", temperature=0.3)
                agents["expense"] = ExpenseClassifierAgent(llm, agent_config)

            if not request.receipt_url:
                raise HTTPException(status_code=400, detail="receipt_url required for expense classifier")

            # Execute agent
            result = await agents["expense"].run(
                receipt_url=request.receipt_url,
                user_id=request.user_id
            )

        else:
            raise HTTPException(status_code=404, detail=f"Agent not found: {request.agent_id}")

        # Record cost (if available)
        if "cost_usd" in result:
            background_tasks.add_task(
                rate_limiter.record_cost,
                request.user_id,
                result["cost_usd"]
            )

        # Create trace URL
        trace_url = None
        if result.get("trace_id"):
            trace_url = langfuse_tracer.get_trace_url(result["trace_id"])

        return AgentRunResponse(
            run_id=run_id,
            agent_id=request.agent_id,
            status="completed" if result.get("answer") or result.get("expense_id") else "failed",
            result=result,
            error=result.get("error"),
            trace_url=trace_url,
            created_at=datetime.utcnow()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        return AgentRunResponse(
            run_id=run_id,
            agent_id=request.agent_id,
            status="error",
            error=str(e),
            created_at=datetime.utcnow()
        )


@app.get("/api/agents/{agent_id}/runs")
async def list_agent_runs(agent_id: str, user_id: Optional[str] = None, limit: int = 50):
    """
    List agent runs.

    Args:
        agent_id: Agent identifier
        user_id: Filter by user (optional)
        limit: Max results

    Returns:
        List of agent runs
    """
    # TODO: Implement run history storage and retrieval
    # For now, return empty list
    return {
        "agent_id": agent_id,
        "runs": [],
        "total": 0
    }


@app.get("/api/stats/rate-limits")
async def get_rate_limit_stats(user_id: Optional[str] = None):
    """Get rate limit statistics."""
    if user_id:
        return rate_limiter.get_user_stats(user_id)
    else:
        return rate_limiter.get_global_stats()


# Run with: uvicorn main:app --reload --host 0.0.0.0 --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
