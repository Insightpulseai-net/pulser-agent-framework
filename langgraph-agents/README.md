# LangGraph Agents

Production-ready LangGraph agent implementations with state machines, tools, and error handling.

## Agent Catalog

### 1. Research Agent
**File**: `agents/research_agent.py`
**Purpose**: Multi-step research with knowledge base retrieval

**State Machine**:
```
Entry → Search Qdrant → Fetch Context → Generate Answer → Validate
  ↑                                                         ↓
  └─────────────────────── Retry ←───────────────────────────┘
```

**Tools**:
- QdrantTool (vector search)
- SupabaseTool (SQL queries)

**Configuration**:
```python
config = {
    "qdrant_url": "http://localhost:6333",
    "supabase_url": "https://xkxyvboeubffxxbebsll.supabase.co",
    "supabase_key": "your-key",
    "confidence_threshold": 0.7,
    "max_retries": 2
}
```

**Example Usage**:
```python
from langchain.chat_models import ChatOpenAI
from agents.research_agent import ResearchAgent

llm = ChatOpenAI(model="gpt-4", temperature=0.7)
agent = ResearchAgent(llm, config)

result = await agent.run(
    query="What are the top expense categories last month?",
    user_id="user-123"
)

print(result["answer"])
print(f"Confidence: {result['confidence']}")
```

---

### 2. Expense Classifier Agent
**File**: `agents/expense_classifier.py`
**Purpose**: OCR → category classification with policy validation

**State Machine**:
```
Entry → OCR Extract → Validate → Classify → Route → Notify
           ↓             ↓
        Error       Quarantine
```

**Tools**:
- PaddleOCR-VL (OCR extraction)
- SupabaseTool (data storage)
- OdooTool (expense creation)

**Configuration**:
```python
config = {
    "supabase_url": "https://xkxyvboeubffxxbebsll.supabase.co",
    "supabase_key": "your-key",
    "odoo_url": "https://odoo.insightpulseai.net",
    "odoo_db": "production",
    "odoo_username": "admin",
    "odoo_password": "your-password",
    "ocr_confidence_threshold": 0.6
}
```

**Example Usage**:
```python
from langchain.chat_models import ChatOpenAI
from agents.expense_classifier import ExpenseClassifierAgent

llm = ChatOpenAI(model="gpt-4", temperature=0.3)
agent = ExpenseClassifierAgent(llm, config)

result = await agent.run(
    receipt_url="https://storage.supabase.co/receipts/sample.jpg",
    user_id="user-123"
)

print(f"Category: {result['category']}")
print(f"Approval Level: {result['approval_level']}")
print(f"Policy Violations: {result['policy_violations']}")
```

---

## Agent Development Guide

### Creating a New Agent

1. **Define State Schema** (`state/agent_state.py`):
```python
class MyAgentState(AgentState, total=False):
    """State for my custom agent."""
    custom_field: str
    custom_data: Dict[str, Any]
```

2. **Build State Machine** (`agents/my_agent.py`):
```python
from langgraph.graph import StateGraph, END
from ..state.agent_state import AgentState

class MyAgent:
    def __init__(self, llm_client, config: Dict[str, Any]):
        self.llm = llm_client
        self.config = config
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("step1", self.step1)
        workflow.add_node("step2", self.step2)

        # Add edges
        workflow.set_entry_point("step1")
        workflow.add_edge("step1", "step2")
        workflow.add_edge("step2", END)

        return workflow.compile()

    async def step1(self, state: AgentState) -> AgentState:
        # Implement step logic
        return state

    async def step2(self, state: AgentState) -> AgentState:
        # Implement step logic
        return state

    async def run(self, input_data: Any, user_id: str) -> Dict[str, Any]:
        initial_state = {
            "user_id": user_id,
            # Initialize state
        }

        final_state = await self.graph.ainvoke(initial_state)
        return final_state
```

3. **Add Tools** (if needed):
```python
from ..tools.supabase_tool import SupabaseTool
from ..tools.qdrant_tool import QdrantTool

self.supabase = SupabaseTool(config["supabase_url"], config["supabase_key"])
self.qdrant = QdrantTool(config["qdrant_url"])
```

4. **Register Agent** (`services/agent-runtime/main.py`):
```python
elif request.agent_id == "my_agent":
    if "my_agent" not in agents:
        from langchain.chat_models import ChatOpenAI
        llm = ChatOpenAI(model="gpt-4", temperature=0.7)
        agents["my_agent"] = MyAgent(llm, agent_config)

    result = await agents["my_agent"].run(...)
```

---

## Testing

### Unit Tests
```bash
pytest tests/test_research_agent.py -v
pytest tests/test_expense_classifier.py -v
```

### Integration Tests
```bash
pytest tests/ -v --cov=langgraph-agents
```

---

## Tools Reference

### SupabaseTool
**File**: `tools/supabase_tool.py`

**Methods**:
- `execute_sql(sql: str)` - Execute arbitrary SQL
- `query_table(table, filters, limit)` - Query with filters
- `insert(table, data)` - Insert row
- `update(table, data, filters)` - Update rows

**Example**:
```python
from tools.supabase_tool import SupabaseTool

supabase = SupabaseTool(url, key)
results = await supabase.execute_sql("SELECT * FROM gold.finance_expenses LIMIT 10")
```

### QdrantTool
**File**: `tools/qdrant_tool.py`

**Methods**:
- `search(collection, query_text, limit, score_threshold)` - Vector search
- `upsert_documents(collection, documents)` - Insert/update docs

**Example**:
```python
from tools.qdrant_tool import QdrantTool

qdrant = QdrantTool(url)
results = await qdrant.search(
    collection_name="knowledge_base",
    query_text="What are BIR filing requirements?",
    limit=5,
    score_threshold=0.7
)
```

### OdooTool
**File**: `tools/odoo_tool.py`

**Methods**:
- `get_expense_categories()` - Get expense categories
- `create_expense(data)` - Create expense record
- `generate_bir_form(type, period, employee)` - Generate BIR form

**Example**:
```python
from tools.odoo_tool import OdooTool

odoo = OdooTool(url, db, username, password)
categories = await odoo.get_expense_categories()
expense_id = await odoo.create_expense(expense_data)
```

---

## Performance

### Latency Targets
- **Agent Execution**: <5s (p95)
- **Vector Search**: <100ms (p95)
- **LLM Call**: <3s (p95)

### Optimization Tips
1. **Parallel Operations**: Use `asyncio.gather()` for independent tool calls
2. **Caching**: Cache frequently accessed data (categories, schemas)
3. **Batch Operations**: Batch multiple SQL queries when possible
4. **Token Optimization**: Use smaller models for simple tasks

---

## Troubleshooting

### Agent Execution Fails
**Symptom**: Agent returns error or times out

**Solutions**:
1. Check tool connectivity (Qdrant, Supabase, Odoo)
2. Verify API keys and credentials
3. Check agent logs for detailed errors
4. Test tools independently

### Low Confidence Scores
**Symptom**: Agent returns low confidence answers

**Solutions**:
1. Improve knowledge base content (more documents)
2. Lower `score_threshold` in Qdrant search
3. Adjust `confidence_threshold` in agent config
4. Add more context to queries

### Rate Limit Exceeded
**Symptom**: HTTP 429 errors

**Solutions**:
1. Check rate limiter settings
2. Upgrade user tier if needed
3. Implement request queuing
4. Add exponential backoff in client

---

## Next Steps

1. Implement Finance SSC Agent (`agents/finance_ssc_agent.py`)
2. Add more tools (Calculator, Web Search)
3. Implement agent run history storage
4. Add human-in-the-loop approval workflows
5. Create agent performance dashboards
