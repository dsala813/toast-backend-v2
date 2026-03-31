from typing import Any
import pandas as pd

FIELD_DICTIONARY: dict[str, dict[str, str]] = {
    "item name": {"standard_field": "item_name", "type": "string", "meaning": "Menu item name", "notes": "common mapping"},
    "menu group": {"standard_field": "menu_group_name", "type": "string", "meaning": "Menu group or section name", "notes": "common mapping"},
    "category": {"standard_field": "menu_category_name", "type": "string", "meaning": "Menu category", "notes": "common mapping"},
    "modifier name": {"standard_field": "modifier_name", "type": "string", "meaning": "Modifier or add-on name", "notes": "common mapping"},
    "price": {"standard_field": "base_price", "type": "number", "meaning": "Base or listed item price", "notes": "confirm currency"},
    "gross sales": {"standard_field": "gross_sales", "type": "number", "meaning": "Sales before discounts and adjustments", "notes": "confirm report semantics"},
    "net sales": {"standard_field": "net_sales", "type": "number", "meaning": "Sales after discounts and adjustments", "notes": "confirm report semantics"},
    "discount amount": {"standard_field": "discount_amount", "type": "number", "meaning": "Discount amount", "notes": "may need sign normalization"},
    "tax": {"standard_field": "tax_amount", "type": "number", "meaning": "Tax amount", "notes": "may exclude service charges"},
    "qty": {"standard_field": "quantity", "type": "number", "meaning": "Quantity sold or ordered", "notes": "coerce numeric"},
    "quantity": {"standard_field": "quantity", "type": "number", "meaning": "Quantity sold or ordered", "notes": "coerce numeric"},
    "order date": {"standard_field": "order_date", "type": "date", "meaning": "Business or order date", "notes": "confirm date semantics"},
    "business date": {"standard_field": "business_date", "type": "date", "meaning": "Operational business date", "notes": "preferred in sales models"},
    "order id": {"standard_field": "order_id", "type": "string", "meaning": "Order identifier", "notes": "may not equal check id"},
    "check number": {"standard_field": "check_number", "type": "string", "meaning": "Human-readable check number", "notes": "not always unique across locations"},
    "location": {"standard_field": "location_name", "type": "string", "meaning": "Location name or store name", "notes": "normalize across sites"},
}

def profile_export(columns: list[str], sample_rows: list[dict[str, Any]]) -> dict[str, Any]:
    field_map = []
    warnings: list[str] = []
    normalized_seen = set()
    for col in columns:
        lookup = FIELD_DICTIONARY.get(col.strip().lower())
        if lookup:
            field_map.append({"source_field": col, "standard_field": lookup["standard_field"], "type": lookup["type"], "meaning": lookup["meaning"], "notes": lookup["notes"]})
            if lookup["standard_field"] in normalized_seen:
                warnings.append(f"Potential duplicate semantic mapping found for column: {col}")
            normalized_seen.add(lookup["standard_field"])
        else:
            field_map.append({"source_field": col, "standard_field": "", "type": "unknown", "meaning": "Unmapped field", "notes": "Needs manual review or extended dictionary support"})

    sample_profile = {}
    if sample_rows:
        df = pd.DataFrame(sample_rows)
        duplicates = int(df.duplicated().sum())
        if duplicates:
            warnings.append(f"{duplicates} duplicate sample rows detected.")
        for col in columns:
            if col not in df.columns:
                continue
            series = df[col]
            nulls = int(series.isna().sum() + (series.astype(str).str.strip() == "").sum())
            distinct = int(series.astype(str).nunique(dropna=True))
            sample_profile[col] = {"null_count": nulls, "distinct_count": distinct, "sample_values": [str(v) for v in series.dropna().astype(str).head(3).tolist()]}
            if len(df) and (nulls / len(df)) >= 0.7:
                warnings.append(f"Null-heavy column detected: {col}")
    return {"field_map": field_map, "warnings": warnings, "sample_profile": sample_profile}
