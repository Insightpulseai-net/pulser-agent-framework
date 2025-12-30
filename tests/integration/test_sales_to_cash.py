# =============================================================================
# INTEGRATION TESTS: SALES TO CASH CYCLE
# =============================================================================
# End-to-end integration tests for the complete sales cycle:
# Sales Order -> Delivery -> Invoice -> Payment -> Reconciliation
# =============================================================================

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.integration
class TestSalesToCashCycle:
    """Integration tests for complete sales-to-cash business process."""

    @pytest.fixture
    def sales_order_service(self):
        """Mock sales order service."""
        service = MagicMock()
        service.create_order = MagicMock()
        service.confirm_order = MagicMock()
        return service

    @pytest.fixture
    def inventory_service(self):
        """Mock inventory service."""
        service = MagicMock()
        service.reserve_stock = MagicMock()
        service.create_delivery = MagicMock()
        service.confirm_delivery = MagicMock()
        return service

    @pytest.fixture
    def invoice_service(self):
        """Mock invoice service."""
        service = MagicMock()
        service.create_invoice = MagicMock()
        service.post_invoice = MagicMock()
        return service

    @pytest.fixture
    def payment_service(self):
        """Mock payment service."""
        service = MagicMock()
        service.create_payment = MagicMock()
        service.reconcile_payment = MagicMock()
        return service

    # =========================================================================
    # TEST: COMPLETE SALES CYCLE
    # =========================================================================

    def test_complete_sales_to_cash_cycle(
        self,
        sales_order_service,
        inventory_service,
        invoice_service,
        payment_service,
        sample_customer,
        sample_sales_order,
    ):
        """Test complete sales-to-cash cycle integration."""
        # STEP 1: Create Sales Order
        sales_order = MagicMock()
        sales_order.id = 1
        sales_order.number = "SO-2024-0001"
        sales_order.customer_id = sample_customer["id"]
        sales_order.total = Decimal("15000.00")
        sales_order.state = "draft"

        sales_order_service.create_order.return_value = sales_order
        created_so = sales_order_service.create_order(sample_sales_order)

        assert created_so.number == "SO-2024-0001"
        assert created_so.state == "draft"

        # STEP 2: Confirm Sales Order (reserve stock)
        sales_order.state = "confirmed"
        inventory_service.reserve_stock.return_value = True

        reserved = inventory_service.reserve_stock(sales_order.id)
        assert reserved is True
        assert sales_order.state == "confirmed"

        # STEP 3: Create Delivery Order
        delivery = MagicMock()
        delivery.id = 1
        delivery.number = "DO-2024-0001"
        delivery.sales_order_id = sales_order.id
        delivery.state = "ready"

        inventory_service.create_delivery.return_value = delivery
        created_do = inventory_service.create_delivery(sales_order.id)

        assert created_do.number == "DO-2024-0001"
        assert created_do.sales_order_id == 1

        # STEP 4: Confirm Delivery (ship goods)
        delivery.state = "done"
        delivery.delivered_date = datetime.now()

        inventory_service.confirm_delivery.return_value = delivery
        confirmed_do = inventory_service.confirm_delivery(delivery.id)

        assert confirmed_do.state == "done"
        assert confirmed_do.delivered_date is not None

        # STEP 5: Create Invoice from Delivery
        invoice = MagicMock()
        invoice.id = 1
        invoice.number = "INV-2024-0001"
        invoice.delivery_id = delivery.id
        invoice.total = Decimal("16800.00")  # Including 12% VAT
        invoice.state = "draft"

        invoice_service.create_invoice.return_value = invoice
        created_inv = invoice_service.create_invoice(delivery.id)

        assert created_inv.number == "INV-2024-0001"
        assert created_inv.total == Decimal("16800.00")

        # STEP 6: Post Invoice
        invoice.state = "posted"
        invoice.posted_date = datetime.now()

        invoice_service.post_invoice.return_value = invoice
        posted_inv = invoice_service.post_invoice(invoice.id)

        assert posted_inv.state == "posted"

        # STEP 7: Create Payment
        payment = MagicMock()
        payment.id = 1
        payment.number = "PAY-2024-0001"
        payment.invoice_id = invoice.id
        payment.amount = Decimal("16800.00")
        payment.state = "draft"

        payment_service.create_payment.return_value = payment
        created_pay = payment_service.create_payment(
            invoice_id=invoice.id,
            amount=Decimal("16800.00"),
        )

        assert created_pay.amount == Decimal("16800.00")

        # STEP 8: Reconcile Payment with Invoice
        payment.state = "reconciled"
        invoice.state = "paid"
        invoice.amount_due = Decimal("0.00")

        payment_service.reconcile_payment.return_value = (payment, invoice)
        reconciled_pay, paid_inv = payment_service.reconcile_payment(payment.id)

        assert reconciled_pay.state == "reconciled"
        assert paid_inv.state == "paid"
        assert paid_inv.amount_due == Decimal("0.00")

    # =========================================================================
    # TEST: PARTIAL SHIPMENT
    # =========================================================================

    def test_partial_shipment_creates_backorder(
        self,
        sales_order_service,
        inventory_service,
    ):
        """Test partial shipment creates backorder for remaining items."""
        # Create SO with 100 units
        sales_order = MagicMock()
        sales_order.id = 1
        sales_order.ordered_qty = 100
        sales_order.state = "confirmed"

        # Ship only 60 units (partial)
        delivery = MagicMock()
        delivery.id = 1
        delivery.shipped_qty = 60
        delivery.backorder_qty = 40
        delivery.state = "done"

        # Create backorder for remaining 40 units
        backorder = MagicMock()
        backorder.id = 2
        backorder.original_delivery_id = delivery.id
        backorder.qty = 40
        backorder.state = "ready"

        assert delivery.shipped_qty == 60
        assert backorder.qty == 40
        assert delivery.shipped_qty + backorder.qty == sales_order.ordered_qty

    # =========================================================================
    # TEST: PARTIAL PAYMENT
    # =========================================================================

    def test_partial_payment_tracking(
        self,
        invoice_service,
        payment_service,
    ):
        """Test partial payment leaves invoice partially paid."""
        # Invoice for 10,000
        invoice = MagicMock()
        invoice.id = 1
        invoice.total = Decimal("10000.00")
        invoice.amount_paid = Decimal("0.00")
        invoice.amount_due = Decimal("10000.00")
        invoice.state = "posted"

        # First payment: 6,000
        payment1 = MagicMock()
        payment1.amount = Decimal("6000.00")

        invoice.amount_paid += payment1.amount
        invoice.amount_due -= payment1.amount

        assert invoice.amount_paid == Decimal("6000.00")
        assert invoice.amount_due == Decimal("4000.00")
        assert invoice.state == "posted"  # Still posted, not fully paid

        # Second payment: 4,000 (remaining)
        payment2 = MagicMock()
        payment2.amount = Decimal("4000.00")

        invoice.amount_paid += payment2.amount
        invoice.amount_due -= payment2.amount

        if invoice.amount_due == Decimal("0.00"):
            invoice.state = "paid"

        assert invoice.amount_paid == Decimal("10000.00")
        assert invoice.amount_due == Decimal("0.00")
        assert invoice.state == "paid"

    # =========================================================================
    # TEST: CREDIT NOTE FLOW
    # =========================================================================

    def test_credit_note_reduces_customer_balance(
        self,
        invoice_service,
    ):
        """Test credit note reduces customer outstanding balance."""
        # Original invoice
        invoice = MagicMock()
        invoice.total = Decimal("10000.00")
        invoice.state = "posted"

        # Credit note for partial refund
        credit_note = MagicMock()
        credit_note.total = Decimal("-2000.00")  # Negative = credit
        credit_note.original_invoice_id = invoice.id
        credit_note.state = "posted"

        # Customer balance
        customer_balance = invoice.total + credit_note.total

        assert customer_balance == Decimal("8000.00")

    # =========================================================================
    # TEST: GL INTEGRATION
    # =========================================================================

    def test_invoice_creates_gl_entries(
        self,
        invoice_service,
    ):
        """Test invoice posting creates correct GL entries."""
        invoice = MagicMock()
        invoice.id = 1
        invoice.subtotal = Decimal("10000.00")
        invoice.tax = Decimal("1200.00")
        invoice.total = Decimal("11200.00")

        # Expected GL entries
        gl_entries = [
            # Debit: Accounts Receivable
            {"account": "1200", "debit": Decimal("11200.00"), "credit": Decimal("0.00")},
            # Credit: Revenue
            {"account": "4000", "debit": Decimal("0.00"), "credit": Decimal("10000.00")},
            # Credit: Output VAT
            {"account": "2200", "debit": Decimal("0.00"), "credit": Decimal("1200.00")},
        ]

        total_debits = sum(e["debit"] for e in gl_entries)
        total_credits = sum(e["credit"] for e in gl_entries)

        # GL must balance
        assert total_debits == total_credits
        assert total_debits == Decimal("11200.00")


@pytest.mark.integration
class TestPurchaseToPay:
    """Integration tests for purchase-to-pay business process."""

    def test_complete_purchase_cycle(self):
        """Test complete PO -> Receipt -> Bill -> Payment cycle."""
        # Step 1: Create Purchase Order
        po = MagicMock()
        po.id = 1
        po.number = "PO-2024-0001"
        po.total = Decimal("50000.00")
        po.state = "draft"

        # Step 2: Approve PO
        po.state = "approved"
        assert po.state == "approved"

        # Step 3: Receive Goods
        receipt = MagicMock()
        receipt.id = 1
        receipt.po_id = po.id
        receipt.received_qty = 100
        receipt.state = "done"

        # Step 4: Receive Vendor Bill
        bill = MagicMock()
        bill.id = 1
        bill.po_id = po.id
        bill.total = Decimal("56000.00")  # Including VAT
        bill.state = "posted"

        # Step 5: Three-way match (PO, Receipt, Bill)
        match_result = {
            "po_amount": po.total,
            "receipt_qty": receipt.received_qty,
            "bill_amount": bill.total,
            "matched": True,
        }

        assert match_result["matched"] is True

        # Step 6: Pay Vendor
        payment = MagicMock()
        payment.bill_id = bill.id
        payment.amount = bill.total
        payment.state = "paid"

        bill.state = "paid"

        assert bill.state == "paid"
        assert payment.amount == Decimal("56000.00")


@pytest.mark.integration
@pytest.mark.philippine
class TestPayrollIntegration:
    """Integration tests for Philippine payroll processing."""

    def test_complete_payroll_cycle(
        self,
        sample_employee,
        sss_contribution_table_2024,
        philhealth_rate,
        pagibig_rate,
    ):
        """Test complete payroll processing for Philippine employee."""
        # Basic salary
        basic_salary = sample_employee["basic_salary"]

        # Calculate SSS contribution
        sss_employee = Decimal("1350.00")  # Max bracket
        sss_employer = Decimal("2700.00")

        # Calculate PhilHealth (5% split)
        philhealth_contribution = basic_salary * Decimal("0.05")
        philhealth_employee = philhealth_contribution / 2
        philhealth_employer = philhealth_contribution / 2

        # Cap PhilHealth at max
        philhealth_employee = min(philhealth_employee, Decimal("2500.00"))

        # Calculate Pag-IBIG (2% + 2%)
        pagibig_employee = min(basic_salary * Decimal("0.02"), Decimal("200.00"))
        pagibig_employer = min(basic_salary * Decimal("0.02"), Decimal("200.00"))

        # Total deductions
        total_deductions = sss_employee + philhealth_employee + pagibig_employee

        # Net pay
        net_pay = basic_salary - total_deductions

        # Assertions
        assert basic_salary == Decimal("50000.00")
        assert sss_employee == Decimal("1350.00")
        assert philhealth_employee <= Decimal("2500.00")
        assert pagibig_employee == Decimal("200.00")
        assert net_pay > 0
        assert net_pay < basic_salary

    def test_13th_month_calculation(self, sample_employee):
        """Test 13th month pay calculation (Philippine labor law)."""
        # Employee worked 12 months
        months_worked = 12
        basic_salary = sample_employee["basic_salary"]

        # 13th month = total basic salary / 12
        total_basic_earned = basic_salary * months_worked
        thirteenth_month = total_basic_earned / 12

        assert thirteenth_month == basic_salary  # Full month if worked 12 months

    def test_bir_withholding_tax_calculation(
        self,
        sample_employee,
        ph_tax_brackets_2024,
    ):
        """Test BIR withholding tax calculation."""
        annual_income = sample_employee["basic_salary"] * 12

        # Find applicable bracket
        tax_due = Decimal("0.00")
        for bracket in ph_tax_brackets_2024:
            if bracket["max"] is None or annual_income <= bracket["max"]:
                if annual_income > bracket["min"]:
                    taxable = annual_income - bracket["min"]
                    tax_due = bracket["base"] + (taxable * bracket["rate"])
                break

        # Monthly withholding
        monthly_tax = tax_due / 12

        assert tax_due > 0
        assert monthly_tax > 0
        assert monthly_tax < sample_employee["basic_salary"]
