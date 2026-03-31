from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

import pandas as pd

from app.config import settings


def ensure_output_dir() -> Path:
    path = settings.output_path
    path.mkdir(parents=True, exist_ok=True)
    return path


def build_output_url(file_name: str) -> str:
    return f"{settings.public_base_url.rstrip('/')}/outputs/{file_name}"


def write_dataframe_csv(df: pd.DataFrame, prefix: str) -> dict[str, Any]:
    ensure_output_dir()
    file_name = f"{prefix}_{uuid.uuid4().hex[:8]}.csv"
    path = settings.output_path / file_name
    df.to_csv(path, index=False)
    return {"name": file_name, "url": build_output_url(file_name), "content_type": "text/csv"}


def write_json(data: Any, prefix: str) -> dict[str, Any]:
    ensure_output_dir()
    file_name = f"{prefix}_{uuid.uuid4().hex[:8]}.json"
    path = settings.output_path / file_name
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"name": file_name, "url": build_output_url(file_name), "content_type": "application/json"}


def write_markdown(text: str, prefix: str) -> dict[str, Any]:
    ensure_output_dir()
    file_name = f"{prefix}_{uuid.uuid4().hex[:8]}.md"
    path = settings.output_path / file_name
    path.write_text(text, encoding="utf-8")
    return {"name": file_name, "url": build_output_url(file_name), "content_type": "text/markdown"}
