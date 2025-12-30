# Comprehensive Testing Framework

This document describes the testing strategy, structure, and execution guidelines for the Pulser Agent Framework with Odoo 18 CE + OCA integration.

## Testing Pyramid

```
                    ┌─────────────┐
                    │    E2E      │  ← 5% (Critical paths only)
                    │   Tests     │
                ┌───┴─────────────┴───┐
                │   Integration Tests │  ← 15% (Service integration)
                │                     │
            ┌───┴─────────────────────┴───┐
            │        API Tests            │  ← 20% (REST endpoints)
            │                             │
        ┌───┴─────────────────────────────┴───┐
        │           Unit Tests                │  ← 60% (Business logic)
        │                                     │
        └─────────────────────────────────────┘
```

## Directory Structure

```
tests/
├── conftest.py              # Global fixtures
├── pytest.ini               # Pytest configuration
├── unit/                    # Unit tests (60%)
│   ├── __init__.py
│   ├── test_invoice_service.py
│   ├── test_payment_service.py
│   ├── test_customer_service.py
│   └── test_tax_calculations.py
├── integration/             # Integration tests (15%)
│   ├── __init__.py
│   ├── test_sales_to_cash.py
│   ├── test_purchase_to_pay.py
│   └── test_payroll_cycle.py
├── api/                     # API tests (20%)
│   ├── __init__.py
│   ├── test_invoice_api.py
│   ├── test_customer_api.py
│   └── test_report_api.py
├── e2e/                     # End-to-end tests (5%)
│   ├── __init__.py
│   └── test_critical_flows.py
├── performance/             # Performance benchmarks
│   ├── __init__.py
│   └── test_benchmarks.py
└── security/                # Security tests
    ├── __init__.py
    └── test_security.py
```

## Test Types

### Unit Tests (`@pytest.mark.unit`)
- Test individual functions and methods in isolation
- Use mocks for external dependencies
- Fast execution (< 1s per test)
- Coverage target: 85%

```python
@pytest.mark.unit
def test_vat_calculation():
    subtotal = Decimal("10000.00")
    vat_rate = Decimal("0.12")
    assert subtotal * vat_rate == Decimal("1200.00")
```

### Integration Tests (`@pytest.mark.integration`)
- Test service interactions
- Use real database connections (test database)
- Test complete business workflows

```python
@pytest.mark.integration
def test_sales_to_cash_cycle():
    # Sales Order → Delivery → Invoice → Payment
    pass
```

### API Tests (`@pytest.mark.api`)
- Test REST API endpoints
- Validate request/response schemas
- Test authentication and authorization
- Test error handling

```python
@pytest.mark.api
def test_create_invoice_endpoint(client, auth_headers):
    response = client.post("/api/invoices", headers=auth_headers, json=data)
    assert response.status_code == 201
```

### E2E Tests (`@pytest.mark.e2e`)
- Test critical user journeys
- Use browser automation (Playwright/Selenium)
- Run against staging environment

### Performance Tests (`@pytest.mark.performance`)
- Benchmark critical operations
- Track P95/P99 latencies
- Memory profiling

### Security Tests (`@pytest.mark.security`)
- SQL injection prevention
- XSS prevention
- Authentication bypass attempts
- Authorization boundary tests

## Philippine Compliance Tests

Tests specific to Philippine regulatory compliance are marked with `@pytest.mark.philippine`:

```python
@pytest.mark.philippine
def test_bir_withholding_tax_brackets():
    """Test 2024 BIR progressive tax calculation."""
    pass

@pytest.mark.philippine
def test_sss_contribution_table():
    """Test SSS contribution bracket lookup."""
    pass
```

## Running Tests

### All Tests
```bash
pytest
```

### By Type
```bash
# Unit tests only
pytest -m unit

# Integration tests
pytest -m integration

# API tests
pytest -m api

# Philippine compliance
pytest -m philippine

# Performance benchmarks
pytest -m performance
```

### With Coverage
```bash
pytest --cov=src --cov-report=html --cov-fail-under=85
```

### Parallel Execution
```bash
pytest -n auto  # Uses all available CPUs
pytest -n 4     # Uses 4 workers
```

### Specific File/Test
```bash
pytest tests/unit/test_invoice_service.py
pytest tests/unit/test_invoice_service.py::TestTaxCalculations::test_philippine_vat_12_percent
```

## Fixtures

### Database Fixtures
- `db_engine` - SQLAlchemy engine
- `db_session` - Database session with auto-rollback
- `mock_db_session` - Mocked session for unit tests

### Authentication Fixtures
- `auth_headers` - Standard user JWT headers
- `admin_headers` - Admin user JWT headers
- `test_user` - Test user object

### Business Entity Fixtures
- `sample_customer` - Test customer data
- `sample_invoice` - Test invoice with lines
- `sample_sales_order` - Test sales order
- `sample_employee` - Test employee (Philippine)

### Philippine Compliance Fixtures
- `ph_tax_brackets_2024` - BIR tax brackets
- `sss_contribution_table_2024` - SSS contribution table
- `philhealth_rate` - PhilHealth rate
- `pagibig_rate` - Pag-IBIG rate

## Performance Thresholds

| Operation | P95 Threshold |
|-----------|---------------|
| DB Read | 50ms |
| DB Write | 100ms |
| API Response | 200ms |
| Invoice Creation | 500ms |
| Report Generation | 5000ms |
| Batch Processing | 10000ms |

## CI/CD Integration

Tests run automatically on:
- Push to `main`, `develop`, `feature/**`, `claude/**`
- Pull requests to `main`, `develop`
- Manual workflow dispatch

### Pipeline Stages
1. **Code Quality** - Ruff linting, Black formatting
2. **Unit Tests** - Fast, isolated tests
3. **Integration Tests** - Service integration
4. **E2E Tests** - Critical path validation
5. **API Tests** - REST endpoint validation
6. **Security Tests** - OWASP checks
7. **Performance Tests** - Benchmark validation

## Writing Tests

### Naming Convention
```
test_<method_name>_<scenario>_<expected_result>
```

Example:
```python
def test_create_invoice_without_customer_returns_422():
    pass
```

### Test Structure (AAA Pattern)
```python
def test_example():
    # Arrange - Set up test data
    invoice_data = {"customer_id": 1, "total": "100.00"}

    # Act - Execute the code under test
    result = create_invoice(invoice_data)

    # Assert - Verify the outcome
    assert result.id is not None
    assert result.state == "draft"
```

### Using Fixtures
```python
def test_invoice_creation(sample_customer, sample_invoice):
    # Fixtures are automatically injected
    assert sample_invoice["customer_id"] == sample_customer["id"]
```

### Parametrized Tests
```python
@pytest.mark.parametrize("amount,expected_vat", [
    (Decimal("1000"), Decimal("120")),
    (Decimal("5000"), Decimal("600")),
    (Decimal("10000"), Decimal("1200")),
])
def test_vat_calculation(amount, expected_vat):
    assert amount * Decimal("0.12") == expected_vat
```

## Mocking Guidelines

### Mock External Services
```python
@patch("services.payment_gateway.process_payment")
def test_payment_processing(mock_process):
    mock_process.return_value = {"status": "success"}
    # Test code here
```

### Mock Database
```python
def test_with_mock_db(mock_db_session):
    mock_db_session.query.return_value.filter.return_value.first.return_value = sample_invoice
    # Test code here
```

## Test Data Management

### Factories
Use factories for generating test data:
```python
class InvoiceFactory:
    @staticmethod
    def create(**kwargs):
        defaults = {
            "number": "INV-2024-0001",
            "customer_id": 1,
            "total": Decimal("10000.00"),
        }
        defaults.update(kwargs)
        return defaults
```

### Database Seeds
Test database is seeded with:
- 10 sample customers
- 5 sample products
- Sample chart of accounts
- Philippine tax configuration

## Debugging Tests

### Verbose Output
```bash
pytest -v
pytest -vv  # Extra verbose
```

### Print Debug Info
```bash
pytest -s  # Show print statements
```

### Stop on First Failure
```bash
pytest -x
```

### Debug with PDB
```bash
pytest --pdb  # Drop into debugger on failure
```

## Coverage Reports

### Generate HTML Report
```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### Coverage Thresholds by Module
| Module | Minimum Coverage |
|--------|------------------|
| Core Services | 90% |
| API Endpoints | 85% |
| Business Logic | 85% |
| Utilities | 75% |

## Troubleshooting

### Common Issues

**Database connection errors:**
```bash
# Ensure test database is running
docker-compose up -d test-db
```

**Fixture not found:**
```bash
# Check conftest.py is in the tests directory
# Verify fixture scope is correct
```

**Slow tests:**
```bash
# Profile slow tests
pytest --durations=10
```

## Related Documentation

- [Odoo Testing Guide](https://www.odoo.com/documentation/18.0/developer/tutorials/testing.html)
- [pytest Documentation](https://docs.pytest.org/)
- [Coverage.py](https://coverage.readthedocs.io/)
