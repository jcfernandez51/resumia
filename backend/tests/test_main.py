import httpx
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)
VALID_TEXT = "Este texto tiene suficiente longitud para superar la validación mínima."


def test_health() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_rejects_short_text() -> None:
    response = client.post("/api/summarize", json={"text": "corto"})

    assert response.status_code == 422


def test_requires_groq_configuration(monkeypatch) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    response = client.post("/api/summarize", json={"text": VALID_TEXT})

    assert response.status_code == 503
    assert response.json() == {"detail": "El servicio de IA no está configurado"}


def test_returns_summary_from_groq(monkeypatch) -> None:
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


def test_handles_provider_error(monkeypatch) -> None:
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
