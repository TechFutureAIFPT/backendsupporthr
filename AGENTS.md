# SupportHR Backend & ML Pipeline Agent Rules

These rules apply directly to the Python FastAPI backend and ML Pipeline under `Software/backend/cv-match-api`.

## 1. Scope & Boundaries
- Treat this folder as the Backend service boundary. Main components:
  - `api_server/`: FastAPI endpoints, routers, authentication, OpenAPI schemas.
  - `ml_pipeline/`: CV/JD matching algorithms, scoring models, text extraction.
  - `deploy/`: Docker, Compose, and cloud deployment configs.
- Verify Git root before staging or committing (`Web/BE` has its own Git repository).

## 2. API & Data Contracts
- Treat `api_server` routers and Pydantic schemas as the single source of truth for FE and Mobile.
- Response format standard: `{ "success": boolean, "data": ..., "error": ... }`.
- Validate all incoming payloads with Pydantic; handle exceptions cleanly with standard HTTP status codes.
- Do not hardcode API keys, service account JSONs, or environment configs. Use environment variables.

## 3. Testing & Code Quality
- Run pytest tests before delivering changes.
- Maintain Python clean code standards (type hints, docstrings, modular routers/services).
- Low-churn: Do not alter existing endpoint contracts without updating FE and Mobile specifications.
