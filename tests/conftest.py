# =============================================================================
# PYTEST CONFIGURATION & GLOBAL FIXTURES
# =============================================================================
# Main configuration file for Pulser Agent Framework tests
# Provides shared fixtures, database setup, and test utilities
# =============================================================================

import asyncio
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock

import pytest
from faker import Faker

# Attempt imports - graceful degradation if not installed
try:
    from httpx import AsyncClient
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    import factory
    from factory import Faker as FactoryFaker
    from factory.alchemy import SQLAlchemyModelFactory
    FACTORY_AVAILABLE = True
except ImportError:
    FACTORY_AVAILABLE = False

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker, Session
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False


# =============================================================================
# CONFIGURATION
# =============================================================================

# Test database URL - uses environment variable or defaults to SQLite
TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://test_user:test_password@localhost:5432/test_db"
)

# Redis URL for caching tests
TEST_REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# API base URL for integration tests
TEST_API_URL = os.getenv("API_URL", "http://localhost:8000")


# =============================================================================
# PYTEST PLUGINS & MARKERS
# =============================================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "api: API tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "security: Security tests")
    config.addinivalue_line("markers", "slow: Slow tests (>5s)")
    config.addinivalue_line("markers", "smoke: Smoke tests for quick validation")
    config.addinivalue_line("markers", "critical: Critical path tests")
    config.addinivalue_line("markers", "odoo: Odoo-specific tests")
    config.addinivalue_line("markers", "philippine: Philippine compliance tests")


# =============================================================================
# EVENT LOOP FIXTURE (for async tests)
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# DATABASE FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
def db_engine():
    """Create database engine for test session."""
    if not SQLALCHEMY_AVAILABLE:
        pytest.skip("SQLAlchemy not installed")

    engine = create_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """
    Create a database session for each test.
    Rolls back transaction after each test for isolation.
    """
    if not SQLALCHEMY_AVAILABLE:
        pytest.skip("SQLAlchemy not installed")

    connection = db_engine.connect()
    transaction = connection.begin()

    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def mock_db_session():
    """Mock database session for unit tests without DB."""
    session = MagicMock()
    session.query = MagicMock()
    session.add = MagicMock()
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.close = MagicMock()
    return session


# =============================================================================
# HTTP CLIENT FIXTURES
# =============================================================================

@pytest.fixture
async def async_client() -> AsyncGenerator:
    """Async HTTP client for API tests."""
    if not HTTPX_AVAILABLE:
        pytest.skip("httpx not installed")

    async with AsyncClient(base_url=TEST_API_URL) as client:
        yield client


@pytest.fixture
def api_client():
    """Synchronous HTTP client wrapper."""
    if not HTTPX_AVAILABLE:
        pytest.skip("httpx not installed")

    import httpx
    with httpx.Client(base_url=TEST_API_URL) as client:
        yield client


# =============================================================================
# AUTHENTICATION FIXTURES
# =============================================================================

@pytest.fixture
def auth_headers():
    """Generate authentication headers for API tests."""
    return {
        "Authorization": "Bearer test_token_12345",
        "Content-Type": "application/json",
    }


@pytest.fixture
def admin_headers():
    """Generate admin authentication headers."""
    return {
        "Authorization": "Bearer admin_token_12345",
        "Content-Type": "application/json",
        "X-Admin": "true",
    }


@pytest.fixture
def test_user():
    """Create a test user fixture."""
    return {
        "id": 1,
        "email": "test@example.com",
        "username": "testuser",
        "is_active": True,
        "is_admin": False,
    }


@pytest.fixture
def admin_user():
    """Create an admin user fixture."""
    return {
        "id": 999,
        "email": "admin@example.com",
        "username": "admin",
        "is_active": True,
        "is_admin": True,
    }


# =============================================================================
# DATA FIXTURES - BUSINESS ENTITIES
# =============================================================================

@pytest.fixture
def sample_customer():
    """Sample customer data."""
    return {
        "id": 1,
        "name": "Acme Corporation",
        "email": "contact@acme.com",
        "phone": "+63 2 1234 5678",
        "vat": "123-456-789-000",
        "address": "123 Business St, Makati City, Metro Manila, Philippines",
        "country": "PH",
        "is_active": True,
    }


@pytest.fixture
def sample_invoice():
    """Sample invoice data."""
    return {
        "id": 1,
        "number": "INV-2024-0001",
        "customer_id": 1,
        "date": datetime.now().date(),
        "due_date": (datetime.now() + timedelta(days=30)).date(),
        "lines": [
            {
                "description": "Consulting Services",
                "quantity": 10,
                "unit_price": Decimal("5000.00"),
                "tax_rate": Decimal("0.12"),  # 12% VAT
            },
            {
                "description": "Software License",
                "quantity": 1,
                "unit_price": Decimal("25000.00"),
                "tax_rate": Decimal("0.12"),
            },
        ],
        "subtotal": Decimal("75000.00"),
        "tax_amount": Decimal("9000.00"),
        "total": Decimal("84000.00"),
        "state": "draft",
    }


@pytest.fixture
def sample_sales_order():
    """Sample sales order data."""
    return {
        "id": 1,
        "number": "SO-2024-0001",
        "customer_id": 1,
        "date": datetime.now().date(),
        "expected_delivery": (datetime.now() + timedelta(days=7)).date(),
        "lines": [
            {
                "product_id": 1,
                "product_name": "Widget A",
                "quantity": 100,
                "unit_price": Decimal("150.00"),
            },
        ],
        "total": Decimal("15000.00"),
        "state": "draft",
    }


@pytest.fixture
def sample_employee():
    """Sample employee data for Philippine payroll."""
    return {
        "id": 1,
        "employee_id": "EMP-001",
        "name": "Juan Dela Cruz",
        "email": "juan.delacruz@company.com",
        "department": "Finance",
        "position": "Senior Accountant",
        "hire_date": datetime(2020, 1, 15).date(),
        "salary_grade": 10,
        "basic_salary": Decimal("50000.00"),
        "tin": "123-456-789",
        "sss_number": "34-1234567-8",
        "philhealth_number": "12-123456789-0",
        "pagibig_number": "1234-5678-9012",
    }


@pytest.fixture
def sample_bir_form():
    """Sample BIR form data."""
    return {
        "form_type": "1601-C",
        "period": datetime.now().strftime("%Y-%m"),
        "tin": "123-456-789-000",
        "total_compensation": Decimal("5000000.00"),
        "total_tax_withheld": Decimal("750000.00"),
        "total_employees": 50,
        "filing_date": None,
        "status": "draft",
    }


# =============================================================================
# PHILIPPINE COMPLIANCE FIXTURES
# =============================================================================

@pytest.fixture
def ph_tax_brackets_2024():
    """2024 Philippine progressive tax brackets."""
    return [
        {"min": Decimal("0"), "max": Decimal("250000"), "rate": Decimal("0"), "base": Decimal("0")},
        {"min": Decimal("250000"), "max": Decimal("400000"), "rate": Decimal("0.15"), "base": Decimal("0")},
        {"min": Decimal("400000"), "max": Decimal("800000"), "rate": Decimal("0.20"), "base": Decimal("22500")},
        {"min": Decimal("800000"), "max": Decimal("2000000"), "rate": Decimal("0.25"), "base": Decimal("102500")},
        {"min": Decimal("2000000"), "max": Decimal("8000000"), "rate": Decimal("0.30"), "base": Decimal("402500")},
        {"min": Decimal("8000000"), "max": None, "rate": Decimal("0.35"), "base": Decimal("2202500")},
    ]


@pytest.fixture
def sss_contribution_table_2024():
    """2024 SSS contribution table (partial)."""
    return [
        {"min_salary": Decimal("0"), "max_salary": Decimal("4250"), "employee_share": Decimal("180.00"), "employer_share": Decimal("390.00")},
        {"min_salary": Decimal("4250"), "max_salary": Decimal("4750"), "employee_share": Decimal("202.50"), "employer_share": Decimal("427.50")},
        {"min_salary": Decimal("4750"), "max_salary": Decimal("5250"), "employee_share": Decimal("225.00"), "employer_share": Decimal("465.00")},
        # ... more brackets
        {"min_salary": Decimal("29750"), "max_salary": None, "employee_share": Decimal("1350.00"), "employer_share": Decimal("2700.00")},
    ]


@pytest.fixture
def philhealth_rate():
    """PhilHealth contribution rate (2024: 5% split equally)."""
    return {
        "rate": Decimal("0.05"),
        "employee_share": Decimal("0.025"),
        "employer_share": Decimal("0.025"),
        "min_monthly_contribution": Decimal("500.00"),
        "max_monthly_contribution": Decimal("5000.00"),
    }


@pytest.fixture
def pagibig_rate():
    """Pag-IBIG contribution rates."""
    return {
        "employee_rate": Decimal("0.02"),
        "employer_rate": Decimal("0.02"),
        "max_contribution": Decimal("200.00"),
    }


# =============================================================================
# FAKER & FACTORY FIXTURES
# =============================================================================

@pytest.fixture
def fake():
    """Faker instance for generating test data."""
    return Faker(["en_PH", "en_US"])


@pytest.fixture
def generate_customers(fake):
    """Factory function to generate multiple customers."""
    def _generate(count: int = 10):
        customers = []
        for i in range(count):
            customers.append({
                "id": i + 1,
                "name": fake.company(),
                "email": fake.company_email(),
                "phone": fake.phone_number(),
                "vat": f"{fake.random_int(100, 999)}-{fake.random_int(100, 999)}-{fake.random_int(100, 999)}-000",
                "address": fake.address(),
                "country": "PH",
                "is_active": True,
            })
        return customers
    return _generate


@pytest.fixture
def generate_invoices(fake, generate_customers):
    """Factory function to generate multiple invoices."""
    def _generate(count: int = 10):
        customers = generate_customers(count)
        invoices = []
        for i in range(count):
            subtotal = Decimal(str(fake.random_int(10000, 500000)))
            tax = subtotal * Decimal("0.12")
            invoices.append({
                "id": i + 1,
                "number": f"INV-2024-{str(i + 1).zfill(4)}",
                "customer_id": customers[i]["id"],
                "date": fake.date_between(start_date="-30d", end_date="today"),
                "due_date": fake.date_between(start_date="today", end_date="+30d"),
                "subtotal": subtotal,
                "tax_amount": tax,
                "total": subtotal + tax,
                "state": fake.random_element(["draft", "posted", "paid"]),
            })
        return invoices
    return _generate


# =============================================================================
# UTILITY FIXTURES
# =============================================================================

@pytest.fixture
def freeze_time():
    """Fixture to freeze time for deterministic tests."""
    try:
        from freezegun import freeze_time as freezer
        return freezer
    except ImportError:
        pytest.skip("freezegun not installed")


@pytest.fixture
def mock_external_api():
    """Mock external API responses."""
    responses = {
        "bir_validation": {"valid": True, "tin_status": "active"},
        "sss_validation": {"valid": True, "member_status": "active"},
    }
    return MagicMock(return_value=responses)


@pytest.fixture
def cleanup_test_data(db_session):
    """Cleanup fixture that runs after test."""
    yield
    # Cleanup logic here
    db_session.rollback()


# =============================================================================
# PERFORMANCE FIXTURES
# =============================================================================

@pytest.fixture
def performance_threshold():
    """Define performance thresholds for various operations."""
    return {
        "api_response_p95": 2.0,  # 2 seconds
        "database_query_p95": 0.1,  # 100ms
        "invoice_creation": 1.0,  # 1 second
        "report_generation": 30.0,  # 30 seconds
        "bulk_insert_1000": 5.0,  # 5 seconds for 1000 records
    }


@pytest.fixture
def benchmark_iterations():
    """Number of iterations for benchmark tests."""
    return {
        "quick": 10,
        "standard": 100,
        "thorough": 1000,
    }


# =============================================================================
# TEST OUTPUT HELPERS
# =============================================================================

@pytest.fixture
def test_output_dir(tmp_path):
    """Create a temporary directory for test outputs."""
    output_dir = tmp_path / "test_outputs"
    output_dir.mkdir(exist_ok=True)
    return output_dir


@pytest.fixture
def capture_logs(caplog):
    """Capture and return logs from tests."""
    import logging
    caplog.set_level(logging.DEBUG)
    yield caplog
    # Can analyze caplog.records after test


# =============================================================================
# SKIP CONDITIONS
# =============================================================================

requires_database = pytest.mark.skipif(
    not SQLALCHEMY_AVAILABLE,
    reason="SQLAlchemy not installed"
)

requires_httpx = pytest.mark.skipif(
    not HTTPX_AVAILABLE,
    reason="httpx not installed"
)

requires_factory = pytest.mark.skipif(
    not FACTORY_AVAILABLE,
    reason="factory_boy not installed"
)
