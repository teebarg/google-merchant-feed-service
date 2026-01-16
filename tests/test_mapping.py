from src.sync import build_row_for_sheet, map_product_to_header


class TestMapProductToHeader:
    """Tests for map_product_to_header function."""

    def test_basic_product_mapping(self, mock_product):
        """Test basic product field mapping."""
        assert map_product_to_header(mock_product, "id") == "SKU-001"
        assert map_product_to_header(mock_product, "title") == "Test Product"
        assert map_product_to_header(mock_product, "description") == "A test product description"
        assert map_product_to_header(mock_product, "link") == "https://www.revoque.com.ng/products/SKU-001"
        assert map_product_to_header(mock_product, "image link") == "https://example.com/image.jpg"

    def test_price_formatting(self, mock_product):
        """Test price is formatted with currency."""
        assert map_product_to_header(mock_product, "price") == "1000.0 NGN"

    def test_availability_mapping(self, mock_product):
        """Test availability is always in_stock."""
        assert map_product_to_header(mock_product, "availability") == "in_stock"

    def test_condition_mapping(self, mock_product):
        """Test condition mapping."""
        assert map_product_to_header(mock_product, "condition") == "new"

        used_product = {**mock_product, "condition": "used"}
        assert map_product_to_header(used_product, "condition") == "used"

    def test_optional_fields(self, mock_product):
        """Test optional fields with values."""
        assert map_product_to_header(mock_product, "color") == "Red"
        assert map_product_to_header(mock_product, "size") == "M"
        assert map_product_to_header(mock_product, "age group") == "adult"

    def test_empty_optional_fields(self):
        """Test optional fields with None/empty values."""
        product = {
            "id": "SKU-001",
            "title": "Test",
            "description": "",
            "link": "https://example.com",
            "image link": "",
            "price": 100.0,
            "condition": "new",
            "color": None,
            "size": None,
            "age group": None,
        }
        assert map_product_to_header(product, "color") == ""
        assert map_product_to_header(product, "size") == ""
        assert map_product_to_header(product, "age group") == ""

    def test_fixed_fields(self, mock_product):
        """Test fields with fixed values."""
        assert map_product_to_header(mock_product, "brand") == "Revoque"
        assert map_product_to_header(mock_product, "gender") == "female"
        assert map_product_to_header(mock_product, "material") == "100% Cotton"
        assert map_product_to_header(mock_product, "adult") == "no"
        assert map_product_to_header(mock_product, "identifier exists") == "no"
        assert map_product_to_header(mock_product, "multipack") == "1"
        assert map_product_to_header(mock_product, "is bundle") == "no"
        assert map_product_to_header(mock_product, "sell on google quantity") == "1"

    def test_unknown_header(self, mock_product):
        """Test that unknown headers return empty string."""
        assert map_product_to_header(mock_product, "unknown_field") == ""


class TestBuildRowForSheet:
    """Tests for build_row_for_sheet function."""

    def test_build_row_with_all_headers(self, mock_product, mock_headers):
        """Test building a row with all expected headers."""
        row = build_row_for_sheet(mock_product, mock_headers)

        assert len(row) == len(mock_headers)
        assert row[0] == "SKU-001"  # id
        assert row[1] == "Test Product"  # title
        assert row[6] == "1000.0 NGN"  # price

    def test_build_row_with_subset_headers(self, mock_product):
        """Test building a row with a subset of headers."""
        headers = ["id", "title", "price", "availability"]
        row = build_row_for_sheet(mock_product, headers)

        assert len(row) == 4
        assert row[0] == "SKU-001"
        assert row[1] == "Test Product"
        assert row[2] == "1000.0 NGN"
        assert row[3] == "in_stock"

    def test_build_row_preserves_order(self, mock_product, mock_headers):
        """Test that row order matches header order."""
        row = build_row_for_sheet(mock_product, mock_headers)

        for i, header in enumerate(mock_headers):
            expected_value = map_product_to_header(mock_product, header)
            assert row[i] == expected_value

    def test_build_row_with_empty_product(self, mock_headers):
        """Test building row with minimal product data."""
        minimal_product = {
            "id": "SKU-001",
            "title": "Minimal",
            "description": "",
            "link": "",
            "image link": "",
            "price": 0.0,
            "condition": "new",
            "color": None,
            "size": None,
            "age group": None,
        }

        row = build_row_for_sheet(minimal_product, mock_headers)
        assert len(row) == len(mock_headers)
        assert row[0] == "SKU-001"
        assert row[1] == "Minimal"
