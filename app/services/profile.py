from typing import Any

FIELD_DICTIONARY: dict[str, dict[str, str]] = {
    "item name": {"standard_field": "item_name", "type": "string", "meaning": "Menu item name", "notes": "common mapping"},
    "menu group": {"standard_field": "menu_group_name", "type": "string", "meaning": "Menu group or section name", "notes": "common mapping"},
    "category": {"standard_field": "menu_category_name", "type": "string", "meaning": "Menu category", "notes": "common mapping"},
    "modifier group": {"standard_field": "modifier_group_name", "type": "string", "meaning": "Modifier group label", "notes": "may vary by export"},
    "modifier name": {"standard_field": "modifier_name", "type": "string", "meaning": "Modifier or add-on name", "notes": "common mapping"},
    "price": {"standard_field": "base_price", "type": "number", "meaning": "Base or listed item price", "notes": "confirm currency"},
    "gross sales": {"standard_field": "gross_sales", "type": "number", "meaning": "Sales before discounts and adjustments", "notes": "confirm report semantics"},
    "net sales": {"standard_field": "net_sales", "type": "number", "meaning": "Sales after discounts and adjustments", "notes": "confirm report semantics"},
    "discount amount": {"standard_field": "discount_amount", "type": "number", "meaning": "Discount amount applied at row or summary level", "notes": "may need sign normalization"},
    "tax": {"standard_field": "tax_amount", "type": "number", "meaning": "Tax amount", "notes": "may exclude service charges"},
    "service charge": {"standard_field": "service_charge_amount", "type": "number", "meaning": "Service charge or fee amount", "notes": "distinguish from tax"},
    "qty": {"standard_field": "quantity", "type": "number", "meaning": "Quantity sold or ordered", "notes": "coerce numeric"},
    "quantity": {"standard_field": "quantity", "type": "number", "meaning": "Quantity sold or ordered", "notes": "coerce numeric"},
    "order date": {"standard_field": "order_date", "type": "date", "meaning": "Business or order date", "notes": "confirm date semantics"},
    "business date": {"standard_field": "business_date", "type": "date", "meaning": "Operational business date", "notes": "preferred in sales models"},
    "order id": {"standard_field": "order_id", "type": "string", "meaning": "Order identifier", "notes": "may not equal check id"},
    "check id": {"standard_field": "check_id", "type": "string", "meaning": "Check identifier", "notes": "distinct from order id in some exports"},
    "check number": {"standard_field": "check_number", "type": "string", "meaning": "Human-readable check number", "notes": "not always unique across locations"},
    "location": {"standard_field": "location_name", "type": "string", "meaning": "Location name or store name", "notes": "normalize across sites"},
    "employee id": {"standard_field": "employee_id", "type": "string", "meaning": "Employee identifier", "notes": "sensitive in some workflows"},
    "employee name": {"standard_field": "employee_name", "type": "string", "meaning": "Employee name", "notes": "redact for AI uploads when possible"},
    "clock in": {"standard_field": "clock_in_ts", "type": "datetime", "meaning": "Shift clock-in timestamp", "notes": "normalize timezone"},
    "clock out": {"standard_field": "clock_out_ts", "type": "datetime", "meaning": "Shift clock-out timestamp", "notes": "normalize timezone"},
    "hours": {"standard_field": "hours_worked", "type": "number", "meaning": "Hours worked", "notes": "coerce numeric"},
    "tender type": {"standard_field": "tender_type", "type": "string", "meaning": "Payment tender category", "notes": "standardize labels"},
    "tip amount": {"standard_field": "tip_amount", "type": "number", "meaning": "Tip amount", "notes": "confirm if included in tender total"},
    "refund amount": {"standard_field": "refund_amount", "type": "number", "meaning": "Refund amount", "notes": "normalize sign convention"},
    "void flag": {"standard_field": "void_flag", "type": "boolean", "meaning": "Indicates voided row or transaction", "notes": "derive if absent"},
}


def profile_export(columns: list[str], sample_rows: list[dict[str, Any]]) -> dict[str, Any]:
    field_map = []
    warnings: list[str] = []
    normalized_seen = set()

    for col in columns:
        lookup = FIELD_DICTIONARY.get(col.strip().lower())
        if lookup:
            field_map.append({
                "source_field": col,
                "standard_field": lookup["standard_field"],
                "type": lookup["type"],
                "meaning": lookup["meaning"],
                "notes": lookup["notes"],
            })
            if lookup["standard_field"] in normalized_seen:
                warnings.append(f"Potential duplicate semantic mapping found for column: {col}")
            normalized_seen.add(lookup["standard_field"])
        else:
            field_map.append({
                "source_field": col,
                "standard_field": "",
                "type": "unknown",
                "meaning": "Unmapped field",
                "notes": "Needs manual review or extended dictionary support",
            })

    if sample_rows:
        row_count = len(sample_rows)
        null_heavy_columns = []
        for col in columns:
            nulls = sum(1 for row in sample_rows if row.get(col) in (None, "", "null", "NULL"))
            if row_count and (nulls / row_count) >= 0.7:
                null_heavy_columns.append(col)
        if null_heavy_columns:
            warnings.append("Null-heavy sample columns detected: " + ", ".join(null_heavy_columns))

    return {"field_map": field_map, "warnings": warnings}
