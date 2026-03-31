# Toast Data Middleware API v2

Deployable FastAPI starter for a Custom GPT that analyzes and converts Toast POS exports.

## What's new in v2
- Environment-based configuration
- API key from `.env`
- File upload support
- URL ingestion support
- Real output files written to storage
- Download endpoint for generated artifacts
- OpenAPI export endpoint
- Render and Railway starter config
- CORS via env config

## Endpoints
- `GET /health`
- `GET /openapi-actions.yaml`
- `POST /toast/detect-export-type`
- `POST /toast/profile-export`
- `POST /toast/normalize/item-sales`
- `POST /toast/package/knowledge`
- `POST /toast/upload-and-normalize/item-sales`
- `POST /toast/upload-and-package/knowledge`
- `GET /outputs/{file_name}`

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## Auth
All protected endpoints require:

```bash
X-API-Key: change-me-in-production
```

## Local test
Open:
- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/openapi-actions.yaml`

## Production notes
Before using with GPT Actions:
1. Deploy to a public HTTPS URL
2. Set `PUBLIC_BASE_URL`
3. Change the API key
4. Replace permissive CORS if needed
5. Consider object storage for generated files
6. Add file cleanup policies

## Deployment
This repo includes:
- `render.yaml`
- `railway.json`
- `Procfile`
