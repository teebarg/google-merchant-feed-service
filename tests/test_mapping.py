from sync import build_row

def test_build_row_stock():
    product = (
        1, "Test", "Desc", 100, None, 0,
        "img", "Brand", None, None,
        "Red", "M", "male", "cotton", "plain",
        "shirts", True
    )

    row, _ = build_row(product)
    assert row[3] == "out of stock"
