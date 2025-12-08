"""
Research Agent - Multi-step research with knowledge base retrieval.

Workflow:
Entry → Search Qdrant → Fetch Context → Generate Answer → Validate → Retry (if needed)

Use Cases:
- Analyze Scout transaction trends
- Research BIR filing requirements
- Compare vendors by expense amounts
"""

from typing import Dict, List, Any, Optional
from langgraph.graph import StateGraph, END
from langchain.schema import HumanMessage, SystemMessage
import logging

from ..state.agent_state import AgentState
from ..tools.qdrant_tool import QdrantTool
from ..tools.supabase_tool import SupabaseTool

logger = logging.getLogger(__name__)


class ResearchAgent:
    """
    Multi-step research agent with vector search and SQL query capabilities.
    """

    def __init__(self, llm_client, config: Dict[str, Any]):
        self.llm = llm_client
        self.config = config
        self.qdrant = QdrantTool(config["qdrant_url"])
        self.supabase = SupabaseTool(config["supabase_url"], config["supabase_key"])
        self.max_retries = config.get("max_retries", 2)
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine."""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("search", self.search_knowledge_base)
        workflow.add_node("fetch_context", self.fetch_context)
        workflow.add_node("generate", self.generate_answer)
        workflow.add_node("validate", self.validate_answer)
        workflow.add_node("retry", self.retry_logic)

        # Add edges
        workflow.set_entry_point("search")
        workflow.add_edge("search", "fetch_context")
        workflow.add_edge("fetch_context", "generate")
        workflow.add_edge("generate", "validate")

        # Conditional edges
        workflow.add_conditional_edges(
            "validate",
            self.should_retry,
            {
                "retry": "retry",
                "end": END
            }
        )
        workflow.add_edge("retry", "search")

        return workflow.compile()

    async def search_knowledge_base(self, state: AgentState) -> AgentState:
        """
        Step 1: Search Qdrant for relevant documents.
        """
        query = state["messages"][-1].content
        logger.info(f"Searching knowledge base for: {query}")

        try:
            results = await self.qdrant.search(
                collection_name="knowledge_base",
                query_text=query,
                limit=5,
                score_threshold=0.7
            )

            state["search_results"] = results
            state["search_count"] = len(results)
            logger.info(f"Found {len(results)} relevant documents")

        except Exception as e:
            logger.error(f"Qdrant search failed: {e}")
            state["search_results"] = []
            state["search_count"] = 0
            state["error"] = str(e)

        return state

    async def fetch_context(self, state: AgentState) -> AgentState:
        """
        Step 2: Fetch additional context from Supabase if needed.
        """
        query = state["messages"][-1].content

        # Determine if SQL query is needed based on search results
        needs_sql = self._needs_sql_context(query, state["search_results"])

        if needs_sql:
            logger.info("Fetching SQL context from Supabase")
            try:
                sql = self._generate_sql(query)
                results = await self.supabase.execute_sql(sql)
                state["sql_context"] = {
                    "sql": sql,
                    "results": results,
                    "row_count": len(results)
                }
            except Exception as e:
                logger.error(f"SQL execution failed: {e}")
                state["sql_context"] = {"error": str(e)}
        else:
            state["sql_context"] = None

        return state

    async def generate_answer(self, state: AgentState) -> AgentState:
        """
        Step 3: Generate answer using LLM with retrieved context.
        """
        query = state["messages"][-1].content
        search_results = state.get("search_results", [])
        sql_context = state.get("sql_context")

        # Build context from search results
        context = "\n\n".join([
            f"Document {i+1}:\n{doc['text']}"
            for i, doc in enumerate(search_results)
        ])

        # Add SQL results if available
        if sql_context and "results" in sql_context:
            context += f"\n\nSQL Query Results:\n{sql_context['results']}"

        # Build prompt
        system_prompt = """You are a research assistant with access to a knowledge base and database.
Your task is to provide accurate, well-researched answers based on the provided context.

Instructions:
1. Use ONLY the provided context to answer the question
2. If the context is insufficient, say so explicitly
3. Cite sources by referencing document numbers
4. Be concise but thorough
5. If SQL data is provided, summarize key insights"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Context:\n{context}\n\nQuestion: {query}")
        ]

        try:
            response = await self.llm.ainvoke(messages)
            state["answer"] = response.content
            state["confidence"] = self._calculate_confidence(state)
            logger.info(f"Generated answer with confidence: {state['confidence']}")

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            state["answer"] = None
            state["error"] = str(e)
            state["confidence"] = 0.0

        return state

    async def validate_answer(self, state: AgentState) -> AgentState:
        """
        Step 4: Validate answer quality and relevance.
        """
        answer = state.get("answer")
        confidence = state.get("confidence", 0.0)

        validation_result = {
            "has_answer": answer is not None and len(answer) > 20,
            "has_context": state["search_count"] > 0,
            "confidence_threshold": confidence >= self.config.get("confidence_threshold", 0.7),
            "retry_count": state.get("retry_count", 0)
        }

        state["validation"] = validation_result
        state["is_valid"] = all([
            validation_result["has_answer"],
            validation_result["has_context"],
            validation_result["confidence_threshold"]
        ])

        logger.info(f"Validation result: {state['is_valid']}")
        return state

    async def retry_logic(self, state: AgentState) -> AgentState:
        """
        Step 5: Retry logic if validation fails.
        """
        retry_count = state.get("retry_count", 0) + 1
        state["retry_count"] = retry_count

        logger.info(f"Retrying research (attempt {retry_count}/{self.max_retries})")

        # Clear previous results for retry
        state["search_results"] = []
        state["sql_context"] = None
        state["answer"] = None

        return state

    def should_retry(self, state: AgentState) -> str:
        """Determine if we should retry or end."""
        is_valid = state.get("is_valid", False)
        retry_count = state.get("retry_count", 0)

        if not is_valid and retry_count < self.max_retries:
            return "retry"
        return "end"

    def _needs_sql_context(self, query: str, search_results: List[Dict]) -> bool:
        """Determine if SQL context is needed based on query and search results."""
        # Keywords that suggest SQL query is needed
        sql_keywords = [
            "how many", "count", "total", "sum", "average", "top", "bottom",
            "compare", "trend", "over time", "by category", "by vendor",
            "last month", "last year", "this quarter"
        ]

        query_lower = query.lower()
        needs_sql = any(keyword in query_lower for keyword in sql_keywords)

        # If search results are insufficient, try SQL
        if len(search_results) < 2:
            needs_sql = True

        return needs_sql

    def _generate_sql(self, query: str) -> str:
        """
        Generate SQL query from natural language.

        TODO: Replace with LLM-based SQL generation in production.
        """
        # Simplified SQL generation - in production, use LLM
        if "expense" in query.lower():
            return """
            SELECT vendor, SUM(amount) as total, COUNT(*) as count
            FROM gold.finance_expenses
            WHERE date >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY vendor
            ORDER BY total DESC
            LIMIT 10
            """
        elif "transaction" in query.lower():
            return """
            SELECT category, COUNT(*) as count, SUM(amount) as total
            FROM gold.scout_transactions
            WHERE date >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY category
            ORDER BY total DESC
            """
        else:
            # Default query
            return "SELECT * FROM gold.finance_expenses LIMIT 10"

    def _calculate_confidence(self, state: AgentState) -> float:
        """
        Calculate confidence score based on:
        - Number of search results
        - SQL context availability
        - Answer length
        """
        search_count = state.get("search_count", 0)
        sql_context = state.get("sql_context")
        answer = state.get("answer", "")

        confidence = 0.0

        # Search results contribute 40%
        if search_count >= 3:
            confidence += 0.4
        elif search_count >= 1:
            confidence += 0.2

        # SQL context contributes 30%
        if sql_context and "results" in sql_context:
            confidence += 0.3

        # Answer quality contributes 30%
        if len(answer) > 200:
            confidence += 0.3
        elif len(answer) > 100:
            confidence += 0.15

        return round(confidence, 2)

    async def run(self, query: str, user_id: str) -> Dict[str, Any]:
        """
        Execute the research agent workflow.

        Args:
            query: User's research question
            user_id: User identifier for tracking

        Returns:
            Dict with answer, confidence, and metadata
        """
        # Initialize state
        initial_state: AgentState = {
            "messages": [HumanMessage(content=query)],
            "user_id": user_id,
            "search_results": [],
            "search_count": 0,
            "sql_context": None,
            "answer": None,
            "confidence": 0.0,
            "validation": {},
            "is_valid": False,
            "retry_count": 0,
            "error": None
        }

        # Run the graph
        try:
            final_state = await self.graph.ainvoke(initial_state)

            return {
                "answer": final_state.get("answer"),
                "confidence": final_state.get("confidence"),
                "search_results": final_state.get("search_results"),
                "sql_context": final_state.get("sql_context"),
                "validation": final_state.get("validation"),
                "retry_count": final_state.get("retry_count"),
                "error": final_state.get("error")
            }

        except Exception as e:
            logger.error(f"Research agent execution failed: {e}")
            return {
                "answer": None,
                "confidence": 0.0,
                "error": str(e)
            }


# Example usage
if __name__ == "__main__":
    import asyncio
    from langchain.chat_models import ChatOpenAI

    config = {
        "qdrant_url": "http://localhost:6333",
        "supabase_url": "https://xkxyvboeubffxxbebsll.supabase.co",
        "supabase_key": "your-service-role-key",
        "confidence_threshold": 0.7,
        "max_retries": 2
    }

    llm = ChatOpenAI(model="gpt-4", temperature=0.7)
    agent = ResearchAgent(llm, config)

    # Run research query
    result = asyncio.run(agent.run(
        query="What are the top expense categories last month?",
        user_id="user-123"
    ))

    print(f"Answer: {result['answer']}")
    print(f"Confidence: {result['confidence']}")
