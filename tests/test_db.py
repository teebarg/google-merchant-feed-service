import os
from unittest.mock import MagicMock, patch

import pytest

from src.db import fetch_products


class TestFetchProducts:
    """Tests for fetch_products function."""

    @patch("src.db.psycopg2.connect")
    def test_fetch_products_success(self, mock_connect):
        """Test successful product fetching."""
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur

        # Mock database rows
        mock_rows = [
            {
                "id": 1,
                "sku": "SKU-001",
                "title": "Test Product",
                "description": "Test description",
                "price": 1000.0,
                "old_price": 1200.0,
                "image_url": "https://example.com/image.jpg",
                "is_new": True,
                "color": "Red",
                "size": "M",
                "age": "adult",
                "is_active": True,
            },
            {
                "id": 2,
                "sku": "SKU-002",
                "title": "Another Product",
                "description": None,
                "price": 2000.0,
                "old_price": None,
                "image_url": None,
                "is_new": False,
                "color": None,
                "size": None,
                "age": None,
                "is_active": True,
            },
        ]
        mock_cur.fetchall.return_value = mock_rows

        # Set environment variable
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://test:test@localhost/test"}):
            products = fetch_products()

        # Verify connection was made
        mock_connect.assert_called_once_with("postgresql://test:test@localhost/test")
        mock_cur.execute.assert_called_once()

        # Verify products are correctly transformed
        assert len(products) == 2

        # Check first product
        assert products[0]["id"] == "SKU-001"
        assert products[0]["title"] == "Test Product"
        assert products[0]["description"] == "Test description"
        assert products[0]["price"] == 1000.0
        assert products[0]["link"] == "https://www.revoque.com.ng/products/SKU-001"
        assert products[0]["image link"] == "https://example.com/image.jpg"
        assert products[0]["condition"] == "new"
        assert products[0]["color"] == "Red"
        assert products[0]["size"] == "M"
        assert products[0]["age group"] == "adult"
        assert products[0]["is_active"] is True

        # Check second product with None values
        assert products[1]["id"] == "SKU-002"
        assert products[1]["description"] == ""  # None should become empty string
        assert products[1]["image link"] == ""  # None should become empty string
        assert products[1]["condition"] == "used"  # is_new=False
        assert products[1]["color"] == ""  # None should become empty string
        assert products[1]["size"] == ""  # None should become empty string
        assert products[1]["age group"] == ""  # None should become empty string

        # Verify cursor and connection are closed
        mock_cur.close.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("src.db.psycopg2.connect")
    def test_fetch_products_empty_result(self, mock_connect):
        """Test fetching when no products exist."""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchall.return_value = []

        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://test:test@localhost/test"}):
            products = fetch_products()

        assert products == []
        mock_cur.close.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("src.db.psycopg2.connect")
    def test_fetch_products_handles_none_price(self, mock_connect):
        """Test handling of None price values."""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur

        mock_rows = [
            {
                "id": 1,
                "sku": "SKU-001",
                "title": "Test Product",
                "description": "Test",
                "price": None,
                "old_price": None,
                "image_url": None,
                "is_new": True,
                "color": None,
                "size": None,
                "age": None,
                "is_active": True,
            }
        ]
        mock_cur.fetchall.return_value = mock_rows

        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://test:test@localhost/test"}):
            products = fetch_products()

        assert products[0]["price"] == 0.0  # None price should become 0.0

    @patch("src.db.psycopg2.connect")
    def test_fetch_products_connection_error(self, mock_connect):
        """Test handling of database connection errors."""
        mock_connect.side_effect = Exception("Connection failed")

        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://test:test@localhost/test"}):
            with pytest.raises(Exception, match="Connection failed"):
                fetch_products()
