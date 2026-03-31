from typing import Iterable


def _normalize(columns: Iterable[str]) -> set[str]:
    return {c.strip().lower().replace(" ", "_") for c in columns}


def detect_export_type(columns: list[str]) -> tuple[str, str, float, list[str], list[str], list[str]]:
    normalized = _normalize(columns)

    warnings: list[str] = []
    assumptions: list[str] = []
    matched_patterns: list[str] = []

    if {"item_name", "qty", "net_sales"}.issubset(normalized) or {"item_name", "quantity", "net_sales"}.issubset(normalized):
        matched_patterns.append("item_name + quantity + net_sales")
        if "order_date" in normalized or "business_date" in normalized:
            matched_patterns.append("date column present")
        return (
            "toast_item_sales_export",
            "one row per sold menu item",
            0.93,
            warnings,
            assumptions,
            matched_patterns,
        )

    if ("item_name" in normalized or "modifier_name" in normalized) and (
        "menu_group" in normalized or "category" in normalized or "price" in normalized
    ):
        matched_patterns.append("menu structure columns detected")
        return (
            "toast_menu_export",
            "one row per menu entity, item, or modifier depending on report structure",
            0.86,
            warnings,
            assumptions,
            matched_patterns,
        )

    if {"employee_id", "clock_in", "clock_out"}.intersection(normalized) and "hours" in normalized:
        matched_patterns.append("labor fields detected")
        return (
            "toast_labor_export",
            "one row per shift, employee-day, or job segment",
            0.82,
            warnings,
            assumptions,
            matched_patterns,
        )

    if {"business_date", "gross_sales", "net_sales"}.issubset(normalized):
        matched_patterns.append("summary sales metrics detected")
        return (
            "toast_sales_summary_export",
            "one row per date, location, or summary group",
            0.79,
            warnings,
            assumptions,
            matched_patterns,
        )

    assumptions.append("No confident export-family pattern matched; classification is provisional.")
    return (
        "unknown_toast_export",
        "unknown",
        0.35,
        warnings,
        assumptions,
        matched_patterns,
    )
