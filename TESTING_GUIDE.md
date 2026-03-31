# Toast Export Validation Guide

Use 3 real Toast files to validate the GPT and backend.

## File 1: Item Sales Export
Expected:
- `source_type = toast_item_sales_export`
- row grain = one row per sold menu item
- outputs include normalized CSV and profile report

## File 2: Menu Export
Expected:
- `source_type = toast_menu_export`
- output includes markdown summary, manifest, preview JSON

## File 3: Sales Summary Export
Expected:
- `source_type = toast_sales_summary_export`
- row grain = date/location/revenue-center/summary grouping

## Suggested GPT prompts
- Analyze this Toast export for analysis and identify the row grain.
- Profile this Toast export and produce a field mapping table with null and duplicate warnings.
- Package this Toast export for Custom GPT knowledge upload.
