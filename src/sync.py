from src.db import fetch_products
from src.locks import acquire_lock, release_lock
from src.sheets import get_existing_rows, get_sheet

EXPECTED_HEADERS = [
    "id", "title", "description", "availability", "link", "image link", "price",
    "identifier exists", "gtin", "mpn", "brand", "product highlight", "product detail", "additional image link",
    "condition", "adult", "color", "size", "gender", "material", "pattern", "age group", "multipack", "is bundle",
    "unit pricing measure", "unit pricing base measure", "energy efficiency class",
    "min energy efficiency class", "max energy efficiency class", "item group id", "sell on google quantity"
]

def get_headers(sheet):
    return sheet.row_values(1)


def build_row_for_sheet(product, headers):
    row = []

    for header in headers:
        row.append(map_product_to_header(product, header))

    return row


def map_product_to_header(p, header):
    mapping = {
        "id": p["id"],
        "title": p["title"],
        "description": p["description"],
        "availability": "in_stock",
        "link": p["link"],
        "image link": p["image link"] or "https://example.com/default.jpg",
        "price": f"{p['price']} NGN",
        "identifier exists": "no",
        "gtin": "",
        "mpn": "",
        "brand": "Revoque",
        "product highlight": "",
        "product detail": "",
        "additional image link": "",
        "condition": p["condition"],
        "adult": "no",
        "color": p["color"] or "",
        "size": p["size"] or "",
        "gender": "female",
        "material": "100% Cotton",
        "pattern": "",
        "age group": p["age group"] or "",
        "multipack": "1",
        "is bundle": "no",
        "unit pricing measure": "",
        "unit pricing base measure": "",
        "energy efficiency class": "",
        "min energy efficiency class": "",
        "max energy efficiency class": "",
        "item group id": "",
        "sell on google quantity": "1",
    }

    return mapping.get(header, "")


def sync_products():
    if not acquire_lock():
        return {"status": "locked"}

    try:
        sheet = get_sheet()
        headers = get_headers(sheet)
        existing = get_existing_rows(sheet)
        products = fetch_products()

        to_insert = []
        to_update = []
        active_ids = set()

        for p in products:
            row = build_row_for_sheet(p, headers)
            pid = str(p["id"])
            active_ids.add(pid)

            if pid in existing:
                to_update.append((existing[pid], row))
            else:
                to_insert.append(row)

        if to_insert:
            sheet.append_rows(to_insert, value_input_option="RAW")

        for idx, row in to_update:
            sheet.update(
                # [row],
                f"A{idx}:{chr(64 + len(headers))}{idx}",
                [row],
                value_input_option="RAW",
            )

        for pid, idx in existing.items():
            if pid not in active_ids:
                sheet.delete_rows(idx)

        return {
            "inserted": len(to_insert),
            "updated": len(to_update),
            "deleted": max(0, len(existing) - len(active_ids)),
        }
    finally:
        release_lock()
