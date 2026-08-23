from fastapi.testclient import TestClient

from app.main import app


def test_web_frontend_request_id_header_is_allowed_by_cors() -> None:
    client = TestClient(app)
    response = client.options(
        "/health/live",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "accept,x-request-id",
        },
    )

    assert response.status_code == 200
    allowed_headers = response.headers.get("access-control-allow-headers", "").lower()
    assert "x-request-id" in allowed_headers


def test_vercel_and_netlify_and_railway_origins_are_allowed_by_cors() -> None:
    client = TestClient(app)
    for origin in [
        "https://support-hr.vercel.app",
        "https://preview-123.vercel.app",
        "https://app.netlify.app",
        "https://backendsupporthr.up.railway.app",
        "https://myapp.railway.app",
    ]:
        response = client.options(
            "/health/live",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "accept,authorization",
            },
        )
        assert response.status_code == 200, f"CORS failed for {origin}"
        assert response.headers.get("access-control-allow-origin") == origin

