from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse

from app.auth import require_api_key
from app.config import settings
from app.schemas import (
    DetectExportTypeRequest,
    NormalizeItemSalesRequest,
    PackageKnowledgeRequest,
    ProfileExportRequest,
    StandardEnvelope,
)
from app.services.detector import detect_export_type
from app.services.normalize import (
    fetch_dataframe,
    normalize_item_sales_dataframe,
    package_knowledge_from_dataframe,
    read_uploaded_dataframe,
)
from app.services.profile import profile_export
from app.services.storage import build_output_url, ensure_output_dir, write_dataframe_csv, write_json, write_markdown

app = FastAPI(
    title="Toast Data Middleware API",
    version="2.0.0",
    description="Deployable starter API for detecting, profiling, normalizing, and packaging Toast POS exports.",
)

ensure_output_dir()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "version": "2.0.0"}


@app.get("/openapi-actions.yaml", response_class=PlainTextResponse)
async def openapi_actions_yaml() -> str:
    return f"""openapi: 3.1.0
info:
  title: Toast Data Middleware API
  version: 2.0.0
  description: API for detecting, profiling, normalizing, and packaging Toast POS exports.
servers:
  - url: {settings.public_base_url}
components:
  securitySchemes:
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key
  schemas:
    DetectExportTypeRequest:
      type: object
      required: [columns]
      properties:
        columns:
          type: array
          items:
            type: string
        sample_rows:
          type: array
          items:
            type: object
            additionalProperties: true
    ProfileExportRequest:
      type: object
      required: [columns]
      properties:
        columns:
          type: array
          items:
            type: string
        sample_rows:
          type: array
          items:
            type: object
            additionalProperties: true
    NormalizeItemSalesRequest:
      type: object
      required: [file_url]
      properties:
        file_url:
          type: string
          format: uri
        options:
          type: object
          additionalProperties: true
    PackageKnowledgeRequest:
      type: object
      required: [file_url, goal]
      properties:
        file_url:
          type: string
          format: uri
        goal:
          type: string
          enum: [custom_gpt_knowledge, analysis]
        options:
          type: object
          additionalProperties: true
    StandardEnvelope:
      type: object
      properties:
        success:
          type: boolean
        source_type:
          type: string
        row_grain:
          type: string
        warnings:
          type: array
          items:
            type: string
        assumptions:
          type: array
          items:
            type: string
        lineage:
          type: object
          additionalProperties: true
        data:
          type: object
          additionalProperties: true
security:
  - ApiKeyAuth: []
paths:
  /toast/detect-export-type:
    post:
      operationId: detectExportType
      summary: Detect the Toast export type from columns and sample rows.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/DetectExportTypeRequest'
      responses:
        '200':
          description: Export type detected.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/StandardEnvelope'
  /toast/profile-export:
    post:
      operationId: profileExport
      summary: Profile a Toast export and return inferred field mappings.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ProfileExportRequest'
      responses:
        '200':
          description: Export profile returned.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/StandardEnvelope'
  /toast/normalize/item-sales:
    post:
      operationId: normalizeItemSales
      summary: Normalize a Toast item sales export into analysis-ready outputs.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/NormalizeItemSalesRequest'
      responses:
        '200':
          description: Normalized outputs created.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/StandardEnvelope'
  /toast/package/knowledge:
    post:
      operationId: packageKnowledge
      summary: Build Custom GPT knowledge assets from a Toast export.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PackageKnowledgeRequest'
      responses:
        '200':
          description: Knowledge package created.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/StandardEnvelope'
"""


@app.get("/outputs/{file_name}")
async def get_output(file_name: str):
    path = settings.output_path / file_name
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Output file not found")
    return FileResponse(path)


@app.post("/toast/detect-export-type", response_model=StandardEnvelope, dependencies=[Depends(require_api_key)])
async def detect_export_type_endpoint(payload: DetectExportTypeRequest) -> StandardEnvelope:
    source_type, row_grain, confidence, warnings, assumptions, matched_patterns = detect_export_type(payload.columns)
    return StandardEnvelope(
        success=True,
        source_type=source_type,
        row_grain=row_grain,
        warnings=warnings,
        assumptions=assumptions,
        lineage={"transform_version": "2026-03-31.2"},
        data={"confidence": confidence, "matched_patterns": matched_patterns},
    )


@app.post("/toast/profile-export", response_model=StandardEnvelope, dependencies=[Depends(require_api_key)])
async def profile_export_endpoint(payload: ProfileExportRequest) -> StandardEnvelope:
    detected_source_type, row_grain, _, detector_warnings, detector_assumptions, _ = detect_export_type(payload.columns)
    profile = profile_export(payload.columns, payload.sample_rows)
    return StandardEnvelope(
        success=True,
        source_type=detected_source_type,
        row_grain=row_grain,
        warnings=detector_warnings + profile["warnings"],
        assumptions=detector_assumptions,
        lineage={"transform_version": "2026-03-31.2"},
        data={"field_map": profile["field_map"]},
    )


@app.post("/toast/normalize/item-sales", response_model=StandardEnvelope, dependencies=[Depends(require_api_key)])
async def normalize_item_sales_endpoint(payload: NormalizeItemSalesRequest) -> StandardEnvelope:
    df, file_name = await fetch_dataframe(str(payload.file_url))
    result = normalize_item_sales_dataframe(df, file_name, payload.options, settings.max_preview_rows)
    output_csv = write_dataframe_csv(result["df"], "fact_item_sales")
    preview_json = write_json(result["preview_rows"], "fact_item_sales_preview")
    return StandardEnvelope(
        success=True,
        source_type="toast_item_sales_export",
        row_grain="one row per sold menu item",
        warnings=result["warnings"],
        assumptions=result["assumptions"],
        lineage=result["lineage"],
        data={
            "outputs": [output_csv, preview_json],
            "preview_rows": result["preview_rows"],
            "row_count": result["row_count"],
        },
    )


@app.post("/toast/package/knowledge", response_model=StandardEnvelope, dependencies=[Depends(require_api_key)])
async def package_knowledge_endpoint(payload: PackageKnowledgeRequest) -> StandardEnvelope:
    df, file_name = await fetch_dataframe(str(payload.file_url))
    result = package_knowledge_from_dataframe(df, file_name, payload.options, settings.max_preview_rows)
    summary_md = write_markdown(result["summary_markdown"], "export_summary")
    preview_json = write_json(result["record_preview"], "entity_records_preview")
    manifest_json = write_json(result["manifest"], "manifest")
    return StandardEnvelope(
        success=True,
        source_type="toast_knowledge_package",
        row_grain="depends on source export",
        warnings=result["warnings"],
        assumptions=result["assumptions"],
        lineage=result["lineage"],
        data={
            "outputs": [summary_md, preview_json, manifest_json],
            "summary_markdown": result["summary_markdown"],
            "record_preview": result["record_preview"],
        },
    )


@app.post("/toast/upload-and-normalize/item-sales", response_model=StandardEnvelope, dependencies=[Depends(require_api_key)])
async def upload_and_normalize_item_sales(file: UploadFile = File(...)) -> StandardEnvelope:
    df, file_name = await read_uploaded_dataframe(file)
    result = normalize_item_sales_dataframe(df, file_name, {}, settings.max_preview_rows)
    output_csv = write_dataframe_csv(result["df"], "fact_item_sales")
    preview_json = write_json(result["preview_rows"], "fact_item_sales_preview")
    return StandardEnvelope(
        success=True,
        source_type="toast_item_sales_export",
        row_grain="one row per sold menu item",
        warnings=result["warnings"],
        assumptions=result["assumptions"],
        lineage=result["lineage"],
        data={
            "outputs": [output_csv, preview_json],
            "preview_rows": result["preview_rows"],
            "row_count": result["row_count"],
        },
    )


@app.post("/toast/upload-and-package/knowledge", response_model=StandardEnvelope, dependencies=[Depends(require_api_key)])
async def upload_and_package_knowledge(file: UploadFile = File(...)) -> StandardEnvelope:
    df, file_name = await read_uploaded_dataframe(file)
    result = package_knowledge_from_dataframe(df, file_name, {"chunk_by": "category"}, settings.max_preview_rows)
    summary_md = write_markdown(result["summary_markdown"], "export_summary")
    preview_json = write_json(result["record_preview"], "entity_records_preview")
    manifest_json = write_json(result["manifest"], "manifest")
    return StandardEnvelope(
        success=True,
        source_type="toast_knowledge_package",
        row_grain="depends on source export",
        warnings=result["warnings"],
        assumptions=result["assumptions"],
        lineage=result["lineage"],
        data={
            "outputs": [summary_md, preview_json, manifest_json],
            "summary_markdown": result["summary_markdown"],
            "record_preview": result["record_preview"],
        },
    )
