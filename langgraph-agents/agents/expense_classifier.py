"""
Expense Classifier Agent with RAG Integration - Enhanced with Qdrant semantic search.

Workflow:
Entry → OCR Extract → Validate → RAG Classify → Route to Approval → Notify

Enhancements:
- Qdrant vector database for semantic similarity search
- GPT-4o-mini classification with historical context
- Learning from classifications for improved accuracy
- Bronze → Silver layer integration with Medallion architecture
"""

from typing import Dict, List, Any, Optional
from langgraph.graph import StateGraph, END
from langchain.schema import HumanMessage, SystemMessage
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import logging
import json
import openai
from datetime import datetime

from ..state.agent_state import AgentState
from ..tools.supabase_tool import SupabaseTool
from ..tools.odoo_tool import OdooTool

logger = logging.getLogger(__name__)


class ExpenseClassifierAgent:
    """
    OCR-powered expense classification with RAG-enhanced intelligence.

    Architecture:
    - LangGraph workflow for orchestration
    - Qdrant for semantic similarity search
    - GPT-4o-mini for classification with historical context
    - Supabase for Bronze/Silver layer persistence
    """

    def __init__(self, llm_client, config: Dict[str, Any]):
        self.llm = llm_client
        self.config = config
        self.supabase = SupabaseTool(config["supabase_url"], config["supabase_key"])
        self.odoo = OdooTool(
            config["odoo_url"],
            config["odoo_db"],
            config["odoo_username"],
            config["odoo_password"]
        )

        # RAG Integration: Qdrant for semantic search
        self.qdrant = QdrantClient(
            url=config.get("qdrant_url", "http://localhost:6333"),
            api_key=config.get("qdrant_api_key")
        )
        self.collection_name = config.get("qdrant_collection", "expense_classifications")
        self.embedding_model = config.get("embedding_model", "text-embedding-3-small")

        # Initialize Qdrant collection
        self._init_qdrant_collection()

        # Build LangGraph workflow
        self.graph = self._build_graph()

    def _init_qdrant_collection(self):
        """Initialize Qdrant collection for expense embeddings"""
        try:
            self.qdrant.get_collection(self.collection_name)
            logger.info(f"Qdrant collection '{self.collection_name}' exists")
        except Exception:
            # Create collection with vector(1536) for text-embedding-3-small
            self.qdrant.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
            )
            logger.info(f"Created Qdrant collection '{self.collection_name}'")

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine."""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("ocr_extract", self.ocr_extract)
        workflow.add_node("validate", self.validate_extraction)
        workflow.add_node("rag_classify", self.rag_classify)  # Enhanced with RAG
        workflow.add_node("route", self.route_approval)
        workflow.add_node("notify", self.notify_stakeholders)
        workflow.add_node("quarantine", self.quarantine_expense)

        # Add edges
        workflow.set_entry_point("ocr_extract")
        workflow.add_edge("ocr_extract", "validate")

        # Conditional edges after validation
        workflow.add_conditional_edges(
            "validate",
            self.validation_check,
            {
                "valid": "rag_classify",
                "invalid": "quarantine"
            }
        )

        workflow.add_edge("rag_classify", "route")
        workflow.add_edge("route", "notify")
        workflow.add_edge("notify", END)
        workflow.add_edge("quarantine", END)

        return workflow.compile()

    async def ocr_extract(self, state: AgentState) -> AgentState:
        """
        Step 1: Extract text from receipt using PaddleOCR-VL.
        """
        receipt_url = state["receipt_url"]
        logger.info(f"Extracting OCR from: {receipt_url}")

        try:
            # Call OCR service (PaddleOCR-VL)
            ocr_response = await self._call_ocr_service(receipt_url)

            state["ocr_data"] = ocr_response
            state["confidence"] = ocr_response.get("confidence", 0.0)
            logger.info(f"OCR extraction complete (confidence: {state['confidence']})")

        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            state["ocr_data"] = {}
            state["confidence"] = 0.0
            state["error"] = str(e)

        return state

    async def validate_extraction(self, state: AgentState) -> AgentState:
        """
        Step 2: Validate extracted fields meet minimum requirements.
        """
        ocr_data = state.get("ocr_data", {})
        confidence = state.get("confidence", 0.0)

        required_fields = ["vendor", "amount", "date"]
        extracted_fields = list(ocr_data.keys())

        validation_result = {
            "has_required_fields": all(field in extracted_fields for field in required_fields),
            "confidence_threshold": confidence >= self.config.get("ocr_confidence_threshold", 0.6),
            "amount_valid": self._is_valid_amount(ocr_data.get("amount")),
            "date_valid": self._is_valid_date(ocr_data.get("date")),
            "vendor_valid": self._is_valid_vendor(ocr_data.get("vendor"))
        }

        state["validation"] = validation_result
        state["is_valid"] = all(validation_result.values())

        logger.info(f"Validation result: {state['is_valid']}")
        return state

    async def rag_classify(self, state: AgentState) -> AgentState:
        """
        Step 3: RAG-enhanced classification using Qdrant semantic search + GPT-4o-mini.

        Process:
        1. Search for similar expenses in Qdrant
        2. Build enriched context with historical data
        3. Use GPT-4o-mini for classification
        4. Store classification for future learning
        """
        ocr_data = state["ocr_data"]
        vendor = ocr_data.get("vendor", "")
        amount = ocr_data.get("amount", 0)
        description = ocr_data.get("description", f"{vendor} - {amount}")

        logger.info(f"RAG classification for: {description}")

        try:
            # Step 1: Search for similar expenses
            similar_expenses = await self._search_similar_expenses(description, vendor, amount)

            # Step 2: Get category list from Odoo
            categories = await self.odoo.get_expense_categories()

            # Step 3: Build classification prompt with RAG context
            classification_prompt = self._build_rag_prompt(
                description, vendor, amount, similar_expenses, categories
            )

            # Step 4: Classify using GPT-4o-mini
            messages = [
                SystemMessage(content="You are an expert expense classifier for Philippine business operations."),
                HumanMessage(content=classification_prompt)
            ]

            response = await self.llm.ainvoke(messages)
            result_json = json.loads(response.content.strip())

            # Step 5: Store result
            state["category"] = result_json["category"]
            state["classification_confidence"] = result_json["confidence"]
            state["classification_reasoning"] = result_json["reasoning"]
            state["tax_type"] = result_json.get("tax_type")
            state["requires_manual_review"] = result_json.get("requires_review", False)
            state["similar_expenses"] = similar_expenses

            # Step 6: Store classification in Qdrant for learning
            await self._store_classification(state)

            logger.info(f"Classified as: {state['category']} (confidence: {state['classification_confidence']:.2f})")

        except Exception as e:
            logger.error(f"RAG classification failed: {e}")
            state["category"] = "Uncategorized"
            state["classification_confidence"] = 0.0
            state["error"] = str(e)

        return state

    async def _search_similar_expenses(
        self,
        description: str,
        vendor: str,
        amount: float,
        k: int = 5
    ) -> List[Dict]:
        """Search for similar expenses using Qdrant semantic similarity"""
        try:
            # Build query text
            query_text = f"{description} {vendor} {amount}"

            # Generate embedding
            embedding_response = openai.embeddings.create(
                model=self.embedding_model,
                input=query_text
            )
            query_vector = embedding_response.data[0].embedding

            # Search Qdrant
            results = self.qdrant.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=k,
                score_threshold=0.7
            )

            similar_expenses = []
            for result in results:
                similar_expenses.append({
                    "id": result.id,
                    "score": result.score,
                    "category": result.payload.get("category"),
                    "description": result.payload.get("description"),
                    "amount": result.payload.get("amount"),
                    "vendor": result.payload.get("vendor"),
                    "tax_type": result.payload.get("tax_type")
                })

            logger.info(f"Found {len(similar_expenses)} similar expenses")
            return similar_expenses

        except Exception as e:
            logger.error(f"Similar expense search failed: {e}")
            return []

    def _build_rag_prompt(
        self,
        description: str,
        vendor: str,
        amount: float,
        similar_expenses: List[Dict],
        categories: List[Dict]
    ) -> str:
        """Build RAG-enriched classification prompt"""
        similar_context = ""
        if similar_expenses:
            similar_context = "\n### Similar Historical Expenses\n"
            for i, exp in enumerate(similar_expenses, 1):
                similar_context += f"{i}. Category: {exp['category']}, "
                similar_context += f"Description: {exp['description']}, "
                similar_context += f"Amount: PHP {exp['amount']:.2f}, "
                similar_context += f"Similarity: {exp['score']:.2f}\n"

        categories_str = "\n".join([f"- {cat['name']}" for cat in categories])

        prompt = f"""You are an expert expense classifier for Philippine business operations.

### Expense to Classify
- Description: {description}
- Amount: PHP {amount:.2f}
- Vendor: {vendor}

{similar_context}

### Available Categories
{categories_str}

### BIR Tax Compliance
Also determine the applicable Philippine tax type:
- Income Tax Withholding (1601-C)
- VAT (2550Q)
- Expanded Withholding Tax (1601-EQ)
- Final Withholding Tax (1601-FQ)
- None

### Response Format (JSON only)
{{
  "category": "category_name",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation based on similar expenses",
  "tax_type": "tax_type or null",
  "requires_review": true/false
}}

Respond with ONLY valid JSON, no other text."""

        return prompt

    async def _store_classification(self, state: AgentState):
        """Store classification in Qdrant for future learning"""
        try:
            ocr_data = state["ocr_data"]
            vendor = ocr_data.get("vendor", "")
            amount = ocr_data.get("amount", 0)
            description = ocr_data.get("description", f"{vendor} - {amount}")

            # Generate unique ID
            point_id = hash(f"{description}_{datetime.now().isoformat()}_{amount}") % (2**31)

            # Create embedding
            text_for_embedding = f"{description} {vendor}"
            embedding_response = openai.embeddings.create(
                model=self.embedding_model,
                input=text_for_embedding
            )
            embedding = embedding_response.data[0].embedding

            # Store in Qdrant
            self.qdrant.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            "description": description,
                            "amount": amount,
                            "vendor": vendor,
                            "date": ocr_data.get("date"),
                            "category": state["category"],
                            "confidence": state["classification_confidence"],
                            "tax_type": state.get("tax_type"),
                            "ocr_confidence": state.get("confidence"),
                            "stored_at": datetime.now().isoformat()
                        }
                    )
                ]
            )

            logger.info(f"Stored classification in Qdrant (ID: {point_id})")

        except Exception as e:
            logger.error(f"Failed to store classification: {e}")

    async def route_approval(self, state: AgentState) -> AgentState:
        """
        Step 4: Route expense to correct approval workflow based on amount and category.
        """
        amount = state["ocr_data"].get("amount", 0)
        category = state.get("category", "Uncategorized")
        user_id = state.get("user_id")

        # Approval routing logic
        if amount < 1000:
            approval_level = "supervisor"
        elif amount < 5000:
            approval_level = "manager"
        else:
            approval_level = "director"

        # Check policy violations
        violations = await self._check_policy_violations(state)

        state["approval_level"] = approval_level
        state["policy_violations"] = violations
        state["requires_manual_review"] = state.get("requires_manual_review", False) or len(violations) > 0

        logger.info(f"Routed to: {approval_level} (violations: {len(violations)})")

        # Create expense record in Odoo
        try:
            expense_id = await self.odoo.create_expense({
                "vendor": state["ocr_data"]["vendor"],
                "amount": amount,
                "date": state["ocr_data"]["date"],
                "category": category,
                "approval_level": approval_level,
                "submitted_by": user_id,
                "status": "pending_approval" if not violations else "flagged",
                "classification_confidence": state.get("classification_confidence"),
                "tax_type": state.get("tax_type")
            })
            state["expense_id"] = expense_id

            # Also store in Bronze layer for Medallion pipeline
            await self._store_bronze_expense(state)

        except Exception as e:
            logger.error(f"Expense creation failed: {e}")
            state["expense_id"] = None
            state["error"] = str(e)

        return state

    async def _store_bronze_expense(self, state: AgentState):
        """Store expense in Bronze layer for Medallion architecture"""
        try:
            bronze_data = {
                "tenant_id": state.get("tenant_id"),
                "workspace_id": state.get("workspace_id"),
                "raw_payload": json.dumps(state["ocr_data"]),
                "source_system": "ocr",
                "source_id": state.get("expense_id"),
                "metadata": json.dumps({
                    "classification_confidence": state.get("classification_confidence"),
                    "ocr_confidence": state.get("confidence"),
                    "category": state.get("category"),
                    "tax_type": state.get("tax_type"),
                    "requires_review": state.get("requires_manual_review")
                })
            }

            await self.supabase.insert("scout.bronze_expenses", bronze_data)
            logger.info("Stored expense in Bronze layer")

        except Exception as e:
            logger.error(f"Bronze layer storage failed: {e}")

    async def notify_stakeholders(self, state: AgentState) -> AgentState:
        """
        Step 5: Notify approvers and user of expense status.
        """
        approval_level = state.get("approval_level")
        expense_id = state.get("expense_id")
        violations = state.get("policy_violations", [])

        notification = {
            "type": "expense_submitted" if not violations else "expense_flagged",
            "expense_id": expense_id,
            "approval_level": approval_level,
            "category": state.get("category"),
            "amount": state["ocr_data"].get("amount"),
            "confidence": state.get("classification_confidence"),
            "violations": violations
        }

        # Send to Mattermost via n8n webhook
        try:
            await self._send_mattermost_notification(notification)
            state["notification_sent"] = True
            logger.info(f"Notification sent for expense: {expense_id}")

        except Exception as e:
            logger.error(f"Notification failed: {e}")
            state["notification_sent"] = False
            state["error"] = str(e)

        return state

    async def quarantine_expense(self, state: AgentState) -> AgentState:
        """
        Error handling: Quarantine expense for manual review.
        """
        ocr_data = state.get("ocr_data", {})
        validation = state.get("validation", {})

        logger.warning(f"Quarantining expense due to validation failure: {validation}")

        # Store in quarantine table
        try:
            quarantine_id = await self.supabase.insert("scout.bronze_expenses", {
                "tenant_id": state.get("tenant_id"),
                "workspace_id": state.get("workspace_id"),
                "raw_payload": json.dumps(ocr_data),
                "source_system": "ocr",
                "metadata": json.dumps({
                    "status": "quarantined",
                    "validation_result": validation,
                    "reason": "OCR validation failed"
                })
            })

            state["quarantine_id"] = quarantine_id
            state["status"] = "quarantined"

            # Notify admin
            await self._send_mattermost_notification({
                "type": "expense_quarantined",
                "quarantine_id": quarantine_id,
                "reason": validation
            })

        except Exception as e:
            logger.error(f"Quarantine storage failed: {e}")
            state["error"] = str(e)

        return state

    def validation_check(self, state: AgentState) -> str:
        """Determine if expense passes validation."""
        return "valid" if state.get("is_valid", False) else "invalid"

    async def _call_ocr_service(self, receipt_url: str) -> Dict[str, Any]:
        """Call PaddleOCR-VL service."""
        # TODO: Implement actual OCR service call
        # For now, return mock data
        return {
            "vendor": "Sample Vendor",
            "amount": 1250.00,
            "date": "2025-12-01",
            "description": "Professional services",
            "confidence": 0.85,
            "raw_text": "Sample receipt text..."
        }

    def _is_valid_amount(self, amount: Any) -> bool:
        """Validate amount field."""
        try:
            return isinstance(amount, (int, float)) and amount > 0
        except:
            return False

    def _is_valid_date(self, date: Any) -> bool:
        """Validate date field."""
        if not isinstance(date, str):
            return False
        # TODO: Add proper date parsing
        return len(date) >= 8

    def _is_valid_vendor(self, vendor: Any) -> bool:
        """Validate vendor field."""
        return isinstance(vendor, str) and len(vendor) >= 2

    async def _check_policy_violations(self, state: AgentState) -> List[str]:
        """Check for policy violations."""
        violations = []
        amount = state["ocr_data"].get("amount", 0)
        category = state.get("category")

        # Example policy rules
        if amount > 10000:
            violations.append("Amount exceeds PHP 10,000 limit without pre-approval")

        if category == "Entertainment" and amount > 500:
            violations.append("Entertainment expense exceeds PHP 500 limit")

        return violations

    async def _send_mattermost_notification(self, notification: Dict[str, Any]) -> None:
        """Send notification to Mattermost."""
        # TODO: Implement Mattermost webhook call
        logger.info(f"Sending notification: {notification}")

    async def run(self, receipt_url: str, user_id: str, tenant_id: str, workspace_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute the expense classifier workflow.

        Args:
            receipt_url: URL to receipt image
            user_id: User identifier
            tenant_id: Tenant identifier for multi-tenancy
            workspace_id: Workspace identifier (optional)

        Returns:
            Dict with classification result and metadata
        """
        initial_state: AgentState = {
            "receipt_url": receipt_url,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "workspace_id": workspace_id,
            "ocr_data": {},
            "confidence": 0.0,
            "validation": {},
            "is_valid": False,
            "category": None,
            "classification_confidence": 0.0,
            "classification_reasoning": None,
            "tax_type": None,
            "similar_expenses": [],
            "approval_level": None,
            "policy_violations": [],
            "requires_manual_review": False,
            "expense_id": None,
            "notification_sent": False,
            "status": "processing",
            "error": None
        }

        try:
            final_state = await self.graph.ainvoke(initial_state)

            return {
                "status": final_state.get("status", "processed"),
                "expense_id": final_state.get("expense_id"),
                "category": final_state.get("category"),
                "classification_confidence": final_state.get("classification_confidence"),
                "classification_reasoning": final_state.get("classification_reasoning"),
                "tax_type": final_state.get("tax_type"),
                "similar_expenses": final_state.get("similar_expenses", []),
                "approval_level": final_state.get("approval_level"),
                "policy_violations": final_state.get("policy_violations"),
                "requires_manual_review": final_state.get("requires_manual_review"),
                "ocr_confidence": final_state.get("confidence"),
                "quarantine_id": final_state.get("quarantine_id"),
                "error": final_state.get("error")
            }

        except Exception as e:
            logger.error(f"Expense classifier execution failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }


# Example usage
if __name__ == "__main__":
    import asyncio
    from langchain.chat_models import ChatOpenAI

    config = {
        "supabase_url": "https://xkxyvboeubffxxbebsll.supabase.co",
        "supabase_key": "your-service-role-key",
        "odoo_url": "https://odoo.insightpulseai.net",
        "odoo_db": "production",
        "odoo_username": "admin",
        "odoo_password": "your-password",
        "ocr_confidence_threshold": 0.6,
        "qdrant_url": "http://localhost:6333",
        "qdrant_api_key": None,
        "qdrant_collection": "expense_classifications",
        "embedding_model": "text-embedding-3-small"
    }

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    agent = ExpenseClassifierAgent(llm, config)

    result = asyncio.run(agent.run(
        receipt_url="https://storage.supabase.co/receipts/sample.jpg",
        user_id="user-123",
        tenant_id="tenant-uuid-123",
        workspace_id="workspace-uuid-456"
    ))

    print(f"Status: {result['status']}")
    print(f"Category: {result['category']}")
    print(f"Classification Confidence: {result['classification_confidence']:.2f}")
    print(f"Tax Type: {result['tax_type']}")
    print(f"Similar Expenses Found: {len(result['similar_expenses'])}")
    print(f"Approval Level: {result['approval_level']}")
