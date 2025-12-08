"""
Agent State - LangGraph state schemas for agent workflows.
"""

from typing import Dict, List, Any, Optional, TypedDict
from langchain.schema import BaseMessage


class AgentState(TypedDict, total=False):
    """Base state for all agents."""
    messages: List[BaseMessage]
    user_id: str
    session_id: Optional[str]
    error: Optional[str]
    metadata: Dict[str, Any]


class ResearchState(AgentState, total=False):
    """State for research agent."""
    search_results: List[Dict[str, Any]]
    search_count: int
    sql_context: Optional[Dict[str, Any]]
    answer: Optional[str]
    confidence: float
    validation: Dict[str, Any]
    is_valid: bool
    retry_count: int


class ExpenseState(AgentState, total=False):
    """State for expense classifier agent."""
    receipt_url: str
    ocr_data: Dict[str, Any]
    confidence: float
    validation: Dict[str, Any]
    is_valid: bool
    category: Optional[str]
    classification_confidence: float
    approval_level: Optional[str]
    policy_violations: List[str]
    requires_manual_review: bool
    expense_id: Optional[str]
    quarantine_id: Optional[str]
    notification_sent: bool
    status: str


class FinanceState(AgentState, total=False):
    """State for finance SSC agent."""
    bir_form_type: str  # 1601-C, 2550Q, etc.
    period: str  # YYYY-MM or YYYY-Q1
    employee_id: str
    tax_data: Dict[str, Any]
    generated_form: Optional[Dict[str, Any]]
    form_pdf_url: Optional[str]
    validation_result: Dict[str, Any]
    submission_status: str
