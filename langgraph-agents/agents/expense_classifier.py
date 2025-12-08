"""
Expense Classifier Agent - OCR → category classification with policy validation.

Workflow:
Entry → OCR Extract → Validate → Classify Category → Route to Approval → Notify

Use Cases:
- Classify receipts from PaddleOCR-VL
- Route expenses to correct approval workflow
- Flag policy violations
"""

from typing import Dict, List, Any, Optional
from langgraph.graph import StateGraph, END
from langchain.schema import HumanMessage, SystemMessage
import logging
import json

from ..state.agent_state import AgentState
from ..tools.supabase_tool import SupabaseTool
from ..tools.odoo_tool import OdooTool

logger = logging.getLogger(__name__)


class ExpenseClassifierAgent:
    """
    OCR-powered expense classification with policy validation.
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
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine."""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("ocr_extract", self.ocr_extract)
        workflow.add_node("validate", self.validate_extraction)
        workflow.add_node("classify", self.classify_category)
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
                "valid": "classify",
                "invalid": "quarantine"
            }
        )

        workflow.add_edge("classify", "route")
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

    async def classify_category(self, state: AgentState) -> AgentState:
        """
        Step 3: Classify expense category using LLM.
        """
        ocr_data = state["ocr_data"]
        vendor = ocr_data.get("vendor", "")
        amount = ocr_data.get("amount", 0)

        # Get category list from Odoo
        categories = await self.odoo.get_expense_categories()

        # Build classification prompt
        system_prompt = """You are an expense classification expert.
Given a vendor name and amount, classify the expense into the correct category.

Available categories:
{categories}

Instructions:
1. Return ONLY the category name (exact match)
2. If uncertain, return "Uncategorized"
3. Consider vendor name patterns (e.g., "Grab" → "Transportation")
"""

        categories_str = "\n".join([f"- {cat['name']}" for cat in categories])

        messages = [
            SystemMessage(content=system_prompt.format(categories=categories_str)),
            HumanMessage(content=f"Vendor: {vendor}\nAmount: {amount}\n\nCategory:")
        ]

        try:
            response = await self.llm.ainvoke(messages)
            category = response.content.strip()

            # Validate category exists
            valid_categories = [cat["name"] for cat in categories]
            if category not in valid_categories:
                category = "Uncategorized"

            state["category"] = category
            state["classification_confidence"] = 0.9 if category != "Uncategorized" else 0.5
            logger.info(f"Classified as: {category}")

        except Exception as e:
            logger.error(f"Classification failed: {e}")
            state["category"] = "Uncategorized"
            state["classification_confidence"] = 0.0
            state["error"] = str(e)

        return state

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
        state["requires_manual_review"] = len(violations) > 0

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
                "status": "pending_approval" if not violations else "flagged"
            })
            state["expense_id"] = expense_id

        except Exception as e:
            logger.error(f"Expense creation failed: {e}")
            state["expense_id"] = None
            state["error"] = str(e)

        return state

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
            quarantine_id = await self.supabase.insert("bronze.quarantine_expenses", {
                "receipt_url": state["receipt_url"],
                "ocr_data": json.dumps(ocr_data),
                "validation_result": json.dumps(validation),
                "reason": "OCR validation failed",
                "status": "pending_manual_review",
                "user_id": state.get("user_id")
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
            violations.append("Amount exceeds $10,000 limit without pre-approval")

        if category == "Entertainment" and amount > 500:
            violations.append("Entertainment expense exceeds $500 limit")

        return violations

    async def _send_mattermost_notification(self, notification: Dict[str, Any]) -> None:
        """Send notification to Mattermost."""
        # TODO: Implement Mattermost webhook call
        logger.info(f"Sending notification: {notification}")

    async def run(self, receipt_url: str, user_id: str) -> Dict[str, Any]:
        """
        Execute the expense classifier workflow.

        Args:
            receipt_url: URL to receipt image
            user_id: User identifier

        Returns:
            Dict with classification result and metadata
        """
        initial_state: AgentState = {
            "receipt_url": receipt_url,
            "user_id": user_id,
            "ocr_data": {},
            "confidence": 0.0,
            "validation": {},
            "is_valid": False,
            "category": None,
            "classification_confidence": 0.0,
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
                "approval_level": final_state.get("approval_level"),
                "policy_violations": final_state.get("policy_violations"),
                "requires_manual_review": final_state.get("requires_manual_review"),
                "confidence": final_state.get("confidence"),
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
        "ocr_confidence_threshold": 0.6
    }

    llm = ChatOpenAI(model="gpt-4", temperature=0.3)
    agent = ExpenseClassifierAgent(llm, config)

    result = asyncio.run(agent.run(
        receipt_url="https://storage.supabase.co/receipts/sample.jpg",
        user_id="user-123"
    ))

    print(f"Status: {result['status']}")
    print(f"Category: {result['category']}")
    print(f"Approval Level: {result['approval_level']}")
