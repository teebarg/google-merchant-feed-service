from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_product():
    """Sample product data structure."""
    return {
        "id": "SKU-001",
        "title": "Test Product",
        "description": "A test product description",
        "link": "https://www.revoque.com.ng/products/SKU-001",
        "image link": "https://example.com/image.jpg",
        "price": 1000.0,
        "condition": "new",
        "color": "Red",
        "size": "M",
        "age group": "adult",
        "is_active": True,
    }


@pytest.fixture
def mock_products(mock_product):
    """Multiple sample products."""
    return [
        mock_product,
        {
            **mock_product,
            "id": "SKU-002",
            "title": "Another Product",
            "price": 2000.0,
            "color": "Blue",
            "condition": "used",
        },
    ]


@pytest.fixture
def mock_headers():
    """Google Sheets headers."""
    return [
        "id",
        "title",
        "description",
        "availability",
        "link",
        "image link",
        "price",
        "identifier exists",
        "gtin",
        "mpn",
        "brand",
        "product highlight",
        "product detail",
        "additional image link",
        "condition",
        "adult",
        "color",
        "size",
        "gender",
        "material",
        "pattern",
        "age group",
        "multipack",
        "is bundle",
        "unit pricing measure",
        "unit pricing base measure",
        "energy efficiency class",
        "min energy efficiency class",
        "max energy efficiency class",
        "item group id",
        "sell on google quantity",
    ]


@pytest.fixture
def mock_sheet(mock_headers):
    """Mock Google Sheets worksheet."""
    sheet = MagicMock()
    sheet.row_values.return_value = mock_headers
    sheet.get_all_records.return_value = []
    sheet.append_rows = MagicMock()
    sheet.update = MagicMock()
    sheet.delete_rows = MagicMock()
    return sheet


@pytest.fixture
def mock_existing_rows():
    """Mock existing rows in sheet."""
    return {
        "SKU-001": 2,  # Row 2 (1-indexed, but we store as 2 because header is row 1)
        "SKU-003": 3,  # This will be deleted if not in active products
    }


@pytest.fixture
def mock_redis_client():
    """Mock Redis client."""
    redis_client = MagicMock()
    redis_client.set.return_value = True
    redis_client.delete = MagicMock()
    redis_client.hset = MagicMock()
    redis_client.hgetall.return_value = {}
    redis_client.expire = MagicMock()
    return redis_client


@pytest.fixture
def mock_db_connection():
    """Mock PostgreSQL connection."""
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value = cur
    cur.fetchall.return_value = []
    return conn, cur
