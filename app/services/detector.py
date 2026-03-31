from typing import Iterable

def _normalize(columns: Iterable[str]) -> set[str]:
    return {c.strip().lower().replace(" ", "_") for c in columns}

def detect_export_type(columns: list[str]) -> tuple[str, str, float, list[str], list[str], list[str]]:
    normalized = _normalize(columns)
    warnings: list[str] = []
    assumptions: list[str] = []
    matched_patterns: list[str] = []

    if {"item_name", "net_sales"}.issubset(normalized) and ("qty" in normalized or "quantity" in normalized):
        matched_patterns.append("item_name + quantity + net_sales")
        if "order_date" in normalized or "business_date" in normalized:
            matched_patterns.append("presence of a date column")
        return ("toast_item_sales_export", "one row per sold menu item", 0.93, warnings, assumptions, matched_patterns)

    if ("item_name" in normalized or "modifier_name" in normalized) and ("menu_group" in normalized or "category" in normalized or "price" in normalized):
        matched_patterns.append("menu structure columns detected")
        return ("toast_menu_export", "one row per menu entity, item, or modifier depending on report structure", 0.86, warnings, assumptions, matched_patterns)

    if {"business_date", "gross_sales", "net_sales"}.issubset(normalized):
        matched_patterns.append("summary sales metrics detected")
        return ("toast_sales_summary_export", "one row per date, location, revenue center, or summary grouping", 0.81, warnings, assumptions, matched_patterns)

    assumptions.append("No confident export-family pattern matched; classification is provisional.")
    return ("unknown_toast_export", "unknown", 0.35, warnings, assumptions, matched_patterns)
