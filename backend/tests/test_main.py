import httpx
import pytest
from fastapi.testclient import TestClient

from app import main
from app.main import app, require_auth


client = TestClient(app)
VALID_TEXT = "Este texto tiene suficiente longitud para superar la validación mínima."


@pytest.fixture
def authenticated():
    # Solo para los tests de Groq: no contacta con Clerk.
    app.dependency_overrides[require_auth] = lambda: None
    yield
    app.dependency_overrides.clear()


def test_health() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_rejects_short_text(authenticated) -> None:
    response = client.post("/api/summarize", json={"text": "corto"})

    assert response.status_code == 422


def test_requires_groq_configuration(monkeypatch, authenticated) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    response = client.post("/api/summarize", json={"text": VALID_TEXT})

    assert response.status_code == 503
    assert response.json() == {"detail": "El servicio de IA no está configurado"}


def test_returns_summary_from_groq(monkeypatch, authenticated) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    async def fake_post(self, url, **kwargs):
        assert url == "https://api.groq.com/openai/v1/chat/completions"
        assert kwargs["headers"]["Authorization"] == "Bearer test-key"
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "Resumen de prueba."}}]},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    response = client.post("/api/summarize", json={"text": VALID_TEXT})

    assert response.status_code == 200
    assert response.json() == {"summary": "Resumen de prueba."}


def test_handles_provider_error(monkeypatch, authenticated) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    async def fake_post(self, url, **kwargs):
        return httpx.Response(
            429,
            json={"error": {"message": "rate limit"}},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    response = client.post("/api/summarize", json={"text": VALID_TEXT})

    assert response.status_code == 502
    assert response.json() == {"detail": "El proveedor de IA rechazó la petición"}


def test_rejects_request_without_session() -> None:
    response = client.post("/api/summarize", json={"text": VALID_TEXT})

    assert response.status_code == 401
    assert response.json() == {"detail": "Debes iniciar sesión"}


def test_rejects_invalid_session(monkeypatch) -> None:
    monkeypatch.setenv("CLERK_SECRET_KEY", "test-secret")
    monkeypatch.setenv("CLERK_AUTHORIZED_PARTIES", "http://localhost:5173")

    class InvalidSession:
        is_signed_in = False

    monkeypatch.setattr(main, "authenticate_request", lambda request, options: InvalidSession())
    response = client.post(
        "/api/summarize",
        json={"text": VALID_TEXT},
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Sesión no válida o caducada"}
