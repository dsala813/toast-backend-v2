from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse

from app.auth import require_api_key
from app.config import settings
from app.schemas import DetectExportTypeRequest, NormalizeItemSalesRequest, PackageKnowledgeRequest, ProfileExportRequest, StandardEnvelope
from app.services.detector import detect_export_type
from app.services.normalize import fetch_dataframe, normalize_item_sales_dataframe, package_knowledge_from_dataframe, read_uploaded_dataframe
from app.services.profile import profile_export
from app.services.storage import ensure_output_dir, write_dataframe_csv, write_json, write_markdown

app = FastAPI(title="Toast Data Middleware API", version="3.0.0", description="Toast export detection, profiling, normalization, and packaging API.")
ensure_output_dir()
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
async def health():
    return {"status": "ok", "version": "3.0.0"}

@app.get("/openapi-actions.yaml", response_class=PlainTextResponse)
async def openapi_actions_yaml():
    return f"""openapi: 3.1.0
info:
  title: Toast Data Middleware API
  version: 3.0.0
  description: API for detecting and profiling Toast POS exports.
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
      summary: Profile a Toast export and return inferred field mappings and sample diagnostics.
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
"""

@app.get("/outputs/{file_name}")
async def get_output(file_name: str):
    path = settings.output_path / file_name
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Output file not found")
    return FileResponse(path)

@app.post("/toast/detect-export-type", response_model=StandardEnvelope, dependencies=[Depends(require_api_key)])
async def detect_export_type_endpoint(payload: DetectExportTypeRequest):
    source_type, row_grain, confidence, warnings, assumptions, matched_patterns = detect_export_type(payload.columns)
    return StandardEnvelope(success=True, source_type=source_type, row_grain=row_grain, warnings=warnings, assumptions=assumptions, lineage={"transform_version": "2026-03-31.3"}, data={"confidence": confidence, "matched_patterns": matched_patterns})

@app.post("/toast/profile-export", response_model=StandardEnvelope, dependencies=[Depends(require_api_key)])
async def profile_export_endpoint(payload: ProfileExportRequest):
    source_type, row_grain, confidence, warnings, assumptions, matched_patterns = detect_export_type(payload.columns)
    profile = profile_export(payload.columns, payload.sample_rows)
    return StandardEnvelope(success=True, source_type=source_type, row_grain=row_grain, warnings=warnings + profile["warnings"], assumptions=assumptions, lineage={"transform_version": "2026-03-31.3"}, data={"confidence": confidence, "matched_patterns": matched_patterns, "field_map": profile["field_map"], "sample_profile": profile["sample_profile"]})

@app.post("/toast/upload-and-profile", response_model=StandardEnvelope, dependencies=[Depends(require_api_key)])
async def upload_and_profile(file: UploadFile = File(...)):
    df, file_name = await read_uploaded_dataframe(file)
    sample_rows = df.head(settings.max_preview_rows).fillna("").to_dict(orient="records")
    columns = list(df.columns)
    source_type, row_grain, confidence, warnings, assumptions, matched_patterns = detect_export_type(columns)
    profile = profile_export(columns, sample_rows)
    output = write_json({"input_file_name": file_name, "source_type": source_type, "row_grain": row_grain, "field_map": profile["field_map"], "sample_profile": profile["sample_profile"], "matched_patterns": matched_patterns}, "profile_report")
    return StandardEnvelope(success=True, source_type=source_type, row_grain=row_grain, warnings=warnings + profile["warnings"], assumptions=assumptions, lineage={"input_file_name": file_name, "transform_version": "2026-03-31.3"}, data={"confidence": confidence, "outputs": [output], "field_map": profile["field_map"], "sample_profile": profile["sample_profile"]})

@app.post("/toast/upload-and-analyze", response_model=StandardEnvelope, dependencies=[Depends(require_api_key)])
async def upload_and_analyze(file: UploadFile = File(...), goal: str = "analysis"):
    df, file_name = await read_uploaded_dataframe(file)
    columns = list(df.columns)
    source_type, row_grain, confidence, warnings, assumptions, matched_patterns = detect_export_type(columns)
    profile = profile_export(columns, df.head(settings.max_preview_rows).fillna("").to_dict(orient="records"))
    recommended = ["fact_item_sales.csv", "dim_item.csv", "dim_location.csv"] if source_type == "toast_item_sales_export" else ["validation_report.md", "data_dictionary.md"]
    output = write_json({"input_file_name": file_name, "source_type": source_type, "row_grain": row_grain, "goal": goal, "matched_patterns": matched_patterns, "field_map": profile["field_map"], "recommended_outputs": recommended}, "analysis_report")
    return StandardEnvelope(success=True, source_type=source_type, row_grain=row_grain, warnings=warnings + profile["warnings"], assumptions=assumptions, lineage={"input_file_name": file_name, "transform_version": "2026-03-31.3"}, data={"confidence": confidence, "outputs": [output], "recommended_outputs": recommended})

@app.post("/toast/normalize/item-sales", response_model=StandardEnvelope, dependencies=[Depends(require_api_key)])
async def normalize_item_sales_endpoint(payload: NormalizeItemSalesRequest):
    df, file_name = await fetch_dataframe(str(payload.file_url))
    result = normalize_item_sales_dataframe(df, file_name, payload.options, settings.max_preview_rows)
    output_csv = write_dataframe_csv(result["df"], "fact_item_sales")
    preview_json = write_json(result["preview_rows"], "fact_item_sales_preview")
    return StandardEnvelope(success=True, source_type="toast_item_sales_export", row_grain="one row per sold menu item", warnings=result["warnings"], assumptions=result["assumptions"], lineage=result["lineage"], data={"outputs": [output_csv, preview_json], "preview_rows": result["preview_rows"], "row_count": result["row_count"]})

@app.post("/toast/upload-and-normalize/item-sales", response_model=StandardEnvelope, dependencies=[Depends(require_api_key)])
async def upload_and_normalize_item_sales(file: UploadFile = File(...)):
    df, file_name = await read_uploaded_dataframe(file)
    result = normalize_item_sales_dataframe(df, file_name, {}, settings.max_preview_rows)
    output_csv = write_dataframe_csv(result["df"], "fact_item_sales")
    preview_json = write_json(result["preview_rows"], "fact_item_sales_preview")
    return StandardEnvelope(success=True, source_type="toast_item_sales_export", row_grain="one row per sold menu item", warnings=result["warnings"], assumptions=result["assumptions"], lineage=result["lineage"], data={"outputs": [output_csv, preview_json], "preview_rows": result["preview_rows"], "row_count": result["row_count"]})

@app.post("/toast/package/knowledge", response_model=StandardEnvelope, dependencies=[Depends(require_api_key)])
async def package_knowledge_endpoint(payload: PackageKnowledgeRequest):
    df, file_name = await fetch_dataframe(str(payload.file_url))
    result = package_knowledge_from_dataframe(df, file_name, payload.options, settings.max_preview_rows)
    summary_md = write_markdown(result["summary_markdown"], "export_summary")
    preview_json = write_json(result["record_preview"], "entity_records_preview")
    manifest_json = write_json(result["manifest"], "manifest")
    return StandardEnvelope(success=True, source_type="toast_knowledge_package", row_grain="depends on source export", warnings=result["warnings"], assumptions=result["assumptions"], lineage=result["lineage"], data={"outputs": [summary_md, preview_json, manifest_json], "summary_markdown": result["summary_markdown"], "record_preview": result["record_preview"]})

@app.post("/toast/upload-and-package/knowledge", response_model=StandardEnvelope, dependencies=[Depends(require_api_key)])
async def upload_and_package_knowledge(file: UploadFile = File(...)):
    df, file_name = await read_uploaded_dataframe(file)
    result = package_knowledge_from_dataframe(df, file_name, {"chunk_by": "category"}, settings.max_preview_rows)
    summary_md = write_markdown(result["summary_markdown"], "export_summary")
    preview_json = write_json(result["record_preview"], "entity_records_preview")
    manifest_json = write_json(result["manifest"], "manifest")
    return StandardEnvelope(success=True, source_type="toast_knowledge_package", row_grain="depends on source export", warnings=result["warnings"], assumptions=result["assumptions"], lineage=result["lineage"], data={"outputs": [summary_md, preview_json, manifest_json], "summary_markdown": result["summary_markdown"], "record_preview": result["record_preview"]})
