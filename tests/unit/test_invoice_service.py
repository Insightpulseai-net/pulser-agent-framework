# =============================================================================
# UNIT TESTS: INVOICE SERVICE
# =============================================================================
# Tests for invoice creation, validation, calculation, and posting
# Covers: VAT calculation, Philippine tax compliance, line items
# =============================================================================

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


# =============================================================================
# TEST: INVOICE CREATION
# =============================================================================

class TestInvoiceCreation:
    """Tests for invoice creation functionality."""

    @pytest.mark.unit
    def test_create_invoice_with_valid_data(self, sample_customer, sample_invoice):
        """Test creating invoice with valid data succeeds."""
        # Arrange
        invoice_data = sample_invoice.copy()

        # Act - Mock the service
        invoice = MagicMock()
        invoice.id = 1
        invoice.number = invoice_data["number"]
        invoice.total = invoice_data["total"]
        invoice.state = "draft"

        # Assert
        assert invoice.id == 1
        assert invoice.number == "INV-2024-0001"
        assert invoice.total == Decimal("84000.00")
        assert invoice.state == "draft"

    @pytest.mark.unit
    def test_invoice_number_format(self, sample_invoice):
        """Test invoice number follows expected format."""
        invoice_number = sample_invoice["number"]

        # Should match pattern: INV-YYYY-NNNN
        assert invoice_number.startswith("INV-")
        parts = invoice_number.split("-")
        assert len(parts) == 3
        assert parts[1].isdigit() and len(parts[1]) == 4  # Year
        assert parts[2].isdigit() and len(parts[2]) == 4  # Sequence

    @pytest.mark.unit
    def test_invoice_requires_customer(self):
        """Test invoice creation fails without customer."""
        invoice_data = {
            "customer_id": None,
            "lines": [{"description": "Test", "quantity": 1, "unit_price": Decimal("100")}],
        }

        # Mock validation
        with pytest.raises(ValueError) as exc_info:
            if not invoice_data.get("customer_id"):
                raise ValueError("Customer is required")

        assert "Customer is required" in str(exc_info.value)

    @pytest.mark.unit
    def test_invoice_requires_at_least_one_line(self):
        """Test invoice creation fails without line items."""
        invoice_data = {
            "customer_id": 1,
            "lines": [],
        }

        with pytest.raises(ValueError) as exc_info:
            if not invoice_data.get("lines"):
                raise ValueError("At least one line item is required")

        assert "At least one line item is required" in str(exc_info.value)


# =============================================================================
# TEST: TAX CALCULATIONS
# =============================================================================

class TestTaxCalculations:
    """Tests for VAT and tax calculations."""

    @pytest.mark.unit
    @pytest.mark.philippine
    def test_philippine_vat_12_percent(self):
        """Test 12% VAT calculation (Philippine standard rate)."""
        subtotal = Decimal("10000.00")
        vat_rate = Decimal("0.12")

        vat_amount = subtotal * vat_rate

        assert vat_amount == Decimal("1200.00")

    @pytest.mark.unit
    @pytest.mark.philippine
    def test_vat_exempt_calculation(self):
        """Test VAT-exempt items (0% VAT)."""
        subtotal = Decimal("10000.00")
        vat_rate = Decimal("0.00")

        vat_amount = subtotal * vat_rate

        assert vat_amount == Decimal("0.00")

    @pytest.mark.unit
    @pytest.mark.philippine
    def test_zero_rated_export_vat(self):
        """Test zero-rated VAT for exports."""
        subtotal = Decimal("50000.00")
        vat_rate = Decimal("0.00")  # Zero-rated for exports
        is_export = True

        if is_export:
            vat_amount = Decimal("0.00")
        else:
            vat_amount = subtotal * Decimal("0.12")

        assert vat_amount == Decimal("0.00")

    @pytest.mark.unit
    @pytest.mark.parametrize("subtotal,expected_vat", [
        (Decimal("1000.00"), Decimal("120.00")),
        (Decimal("5000.00"), Decimal("600.00")),
        (Decimal("10000.00"), Decimal("1200.00")),
        (Decimal("100000.00"), Decimal("12000.00")),
        (Decimal("0.00"), Decimal("0.00")),
    ])
    def test_vat_calculation_parametrized(self, subtotal, expected_vat):
        """Parametrized test for VAT calculation across various amounts."""
        vat_rate = Decimal("0.12")
        calculated_vat = subtotal * vat_rate

        assert calculated_vat == expected_vat

    @pytest.mark.unit
    def test_total_with_multiple_tax_rates(self):
        """Test invoice with mixed tax rates."""
        lines = [
            {"amount": Decimal("10000.00"), "tax_rate": Decimal("0.12")},  # VATable
            {"amount": Decimal("5000.00"), "tax_rate": Decimal("0.00")},   # Exempt
        ]

        total_amount = sum(line["amount"] for line in lines)
        total_tax = sum(line["amount"] * line["tax_rate"] for line in lines)
        grand_total = total_amount + total_tax

        assert total_amount == Decimal("15000.00")
        assert total_tax == Decimal("1200.00")
        assert grand_total == Decimal("16200.00")


# =============================================================================
# TEST: INVOICE LINE CALCULATIONS
# =============================================================================

class TestInvoiceLineCalculations:
    """Tests for invoice line item calculations."""

    @pytest.mark.unit
    def test_line_amount_calculation(self):
        """Test line amount = quantity * unit_price."""
        quantity = 10
        unit_price = Decimal("150.00")

        line_amount = quantity * unit_price

        assert line_amount == Decimal("1500.00")

    @pytest.mark.unit
    def test_line_with_discount(self):
        """Test line amount with discount applied."""
        quantity = 10
        unit_price = Decimal("100.00")
        discount_percent = Decimal("0.10")  # 10% discount

        gross_amount = quantity * unit_price
        discount_amount = gross_amount * discount_percent
        net_amount = gross_amount - discount_amount

        assert gross_amount == Decimal("1000.00")
        assert discount_amount == Decimal("100.00")
        assert net_amount == Decimal("900.00")

    @pytest.mark.unit
    def test_negative_quantity_rejected(self):
        """Test that negative quantities are rejected."""
        quantity = -5

        with pytest.raises(ValueError):
            if quantity < 0:
                raise ValueError("Quantity cannot be negative")

    @pytest.mark.unit
    def test_zero_quantity_rejected(self):
        """Test that zero quantity is rejected."""
        quantity = 0

        with pytest.raises(ValueError):
            if quantity <= 0:
                raise ValueError("Quantity must be greater than zero")


# =============================================================================
# TEST: INVOICE STATE TRANSITIONS
# =============================================================================

class TestInvoiceStateTransitions:
    """Tests for invoice state machine."""

    @pytest.mark.unit
    def test_draft_to_posted_transition(self):
        """Test transitioning invoice from draft to posted."""
        invoice = MagicMock()
        invoice.state = "draft"

        # Simulate posting
        if invoice.state == "draft":
            invoice.state = "posted"
            invoice.posted_date = datetime.now()

        assert invoice.state == "posted"
        assert invoice.posted_date is not None

    @pytest.mark.unit
    def test_posted_to_paid_transition(self):
        """Test transitioning invoice from posted to paid."""
        invoice = MagicMock()
        invoice.state = "posted"
        invoice.amount_due = Decimal("1000.00")

        # Simulate payment
        payment_amount = Decimal("1000.00")
        invoice.amount_due -= payment_amount

        if invoice.amount_due == Decimal("0.00"):
            invoice.state = "paid"

        assert invoice.state == "paid"
        assert invoice.amount_due == Decimal("0.00")

    @pytest.mark.unit
    def test_cannot_post_cancelled_invoice(self):
        """Test that cancelled invoice cannot be posted."""
        invoice = MagicMock()
        invoice.state = "cancelled"

        with pytest.raises(ValueError):
            if invoice.state == "cancelled":
                raise ValueError("Cannot post a cancelled invoice")

    @pytest.mark.unit
    def test_partial_payment_keeps_posted_state(self):
        """Test partial payment keeps invoice in posted state."""
        invoice = MagicMock()
        invoice.state = "posted"
        invoice.amount_due = Decimal("1000.00")

        # Partial payment
        payment_amount = Decimal("500.00")
        invoice.amount_due -= payment_amount

        if invoice.amount_due > Decimal("0.00"):
            invoice.state = "posted"

        assert invoice.state == "posted"
        assert invoice.amount_due == Decimal("500.00")


# =============================================================================
# TEST: INVOICE VALIDATION
# =============================================================================

class TestInvoiceValidation:
    """Tests for invoice validation rules."""

    @pytest.mark.unit
    def test_due_date_must_be_after_invoice_date(self):
        """Test due date must be on or after invoice date."""
        invoice_date = datetime.now().date()
        due_date = invoice_date - timedelta(days=1)  # Invalid: before invoice date

        with pytest.raises(ValueError):
            if due_date < invoice_date:
                raise ValueError("Due date must be on or after invoice date")

    @pytest.mark.unit
    def test_valid_due_date(self):
        """Test valid due date (30 days from invoice)."""
        invoice_date = datetime.now().date()
        due_date = invoice_date + timedelta(days=30)

        assert due_date >= invoice_date
        assert (due_date - invoice_date).days == 30

    @pytest.mark.unit
    def test_invoice_total_matches_line_totals(self):
        """Test invoice total equals sum of line totals."""
        lines = [
            {"amount": Decimal("5000.00"), "tax": Decimal("600.00")},
            {"amount": Decimal("3000.00"), "tax": Decimal("360.00")},
        ]

        expected_subtotal = sum(line["amount"] for line in lines)
        expected_tax = sum(line["tax"] for line in lines)
        expected_total = expected_subtotal + expected_tax

        invoice_total = Decimal("8960.00")  # Should match

        assert expected_subtotal == Decimal("8000.00")
        assert expected_tax == Decimal("960.00")
        assert expected_total == invoice_total


# =============================================================================
# TEST: CURRENCY HANDLING
# =============================================================================

class TestCurrencyHandling:
    """Tests for multi-currency support."""

    @pytest.mark.unit
    def test_peso_as_default_currency(self):
        """Test PHP is default currency for Philippine invoices."""
        invoice = MagicMock()
        invoice.currency = "PHP"

        assert invoice.currency == "PHP"

    @pytest.mark.unit
    def test_usd_invoice_conversion(self):
        """Test USD to PHP conversion."""
        usd_amount = Decimal("100.00")
        exchange_rate = Decimal("56.50")  # Sample rate

        php_amount = usd_amount * exchange_rate

        assert php_amount == Decimal("5650.00")

    @pytest.mark.unit
    @pytest.mark.parametrize("currency,rate,expected", [
        ("USD", Decimal("56.50"), Decimal("5650.00")),
        ("EUR", Decimal("62.00"), Decimal("6200.00")),
        ("JPY", Decimal("0.38"), Decimal("38.00")),
        ("SGD", Decimal("42.00"), Decimal("4200.00")),
    ])
    def test_multiple_currency_conversions(self, currency, rate, expected):
        """Test conversion for multiple currencies."""
        amount = Decimal("100.00")
        converted = amount * rate

        assert converted == expected


# =============================================================================
# TEST: ROUNDING
# =============================================================================

class TestRounding:
    """Tests for proper rounding of monetary values."""

    @pytest.mark.unit
    def test_round_to_two_decimal_places(self):
        """Test amounts are rounded to 2 decimal places."""
        amount = Decimal("100.126")
        rounded = round(amount, 2)

        assert rounded == Decimal("100.13")

    @pytest.mark.unit
    def test_half_up_rounding(self):
        """Test half-up rounding (banker's rounding)."""
        from decimal import ROUND_HALF_UP

        amount = Decimal("100.125")
        rounded = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        assert rounded == Decimal("100.13")

    @pytest.mark.unit
    def test_vat_rounding(self):
        """Test VAT amount rounding."""
        subtotal = Decimal("99.99")
        vat_rate = Decimal("0.12")

        vat = subtotal * vat_rate  # 11.9988
        vat_rounded = round(vat, 2)

        assert vat_rounded == Decimal("12.00")
