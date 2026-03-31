import io
from typing import Any, Tuple
import httpx, pandas as pd
from fastapi import UploadFile

def _to_snake_case(name: str) -> str:
    return name.strip().lower().replace("/", "_").replace("-", "_").replace(" ", "_")

def _read_tabular_file(file_bytes: bytes, file_name: str) -> pd.DataFrame:
    lower_name = file_name.lower()
    if lower_name.endswith(".csv"):
        return pd.read_csv(io.BytesIO(file_bytes))
    if lower_name.endswith(".xlsx"):
        return pd.read_excel(io.BytesIO(file_bytes))
    raise ValueError("Only CSV and XLSX are supported in this starter.")

async def fetch_dataframe(file_url: str) -> Tuple[pd.DataFrame, str]:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(file_url)
        response.raise_for_status()
        file_name = file_url.rstrip("/").split("/")[-1] or "toast_export.csv"
        return _read_tabular_file(response.content, file_name), file_name

async def read_uploaded_dataframe(upload: UploadFile) -> Tuple[pd.DataFrame, str]:
    content = await upload.read()
    return _read_tabular_file(content, upload.filename or "toast_export.csv"), (upload.filename or "toast_export.csv")

def normalize_item_sales_dataframe(df: pd.DataFrame, file_name: str, options: dict[str, Any], max_preview_rows: int) -> dict[str, Any]:
    warnings, assumptions = [], []
    original_columns = list(df.columns)
    df.columns = [_to_snake_case(c) for c in df.columns]
    if options.get("coerce_numeric", True):
        for col in ["qty", "quantity", "gross_sales", "net_sales", "discount_amount", "tax", "tax_amount", "refund_amount"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
    if options.get("normalize_dates", True):
        for col in ["order_date", "business_date"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d")
    if "item_name" not in df.columns and "item" in df.columns:
        df["item_name"] = df["item"]
        assumptions.append("Mapped 'item' to 'item_name'.")
    if "qty" in df.columns and "quantity" not in df.columns:
        df["quantity"] = df["qty"]
    dups = int(df.duplicated().sum())
    if dups:
        warnings.append(f"{dups} exact duplicate rows detected in normalized data.")
    preview = df.head(max_preview_rows).fillna("").to_dict(orient="records")
    return {"df": df, "warnings": warnings, "assumptions": assumptions, "lineage": {"input_file_name": file_name, "original_columns": original_columns, "normalized_columns": list(df.columns), "transform_version": "2026-03-31.3"}, "preview_rows": preview, "row_count": int(len(df))}

def package_knowledge_from_dataframe(df: pd.DataFrame, file_name: str, options: dict[str, Any], max_preview_rows: int) -> dict[str, Any]:
    df.columns = [_to_snake_case(c) for c in df.columns]
    chunk_by = options.get("chunk_by", "category")
    summary = "\n".join([f"# Knowledge Package Summary for {file_name}", "", f"- Row count: {len(df)}", f"- Column count: {len(df.columns)}", f"- Chunk by: {chunk_by}", "", "## Columns", *[f"- {c}" for c in df.columns]])
    preview = df.head(max_preview_rows).fillna("").to_dict(orient="records")
    manifest = {"source_type": "toast_export", "input_file_name": file_name, "row_count": int(len(df)), "columns": list(df.columns), "chunk_by": chunk_by, "transform_version": "2026-03-31.3"}
    return {"warnings": [], "assumptions": ["Knowledge packaging is starter-level and should be expanded for production semantics."], "lineage": {"input_file_name": file_name, "transform_version": "2026-03-31.3"}, "summary_markdown": summary, "record_preview": preview, "manifest": manifest}
