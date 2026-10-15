import os

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Lee las variables del archivo .env si existe.
load_dotenv()

app = FastAPI(title="Resumia API", version="0.1.0")


class SummarizeRequest(BaseModel):
    text: str = Field(min_length=20, max_length=12_000)


class SummarizeResponse(BaseModel):
    summary: str


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/summarize", response_model=SummarizeResponse)
async def summarize(payload: SummarizeRequest) -> SummarizeResponse:
    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    if not api_key:
        raise HTTPException(status_code=503, detail="El servicio de IA no está configurado")

    request_body = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "Resume el texto en español de forma clara y breve. Devuelve solo el resumen.",
            },
            {"role": "user", "content": payload.text},
        ],
        "temperature": 0.2,
        "max_tokens": 256,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                GROQ_URL,
                json=request_body,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Accept": "application/json",
                },
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail="El proveedor de IA rechazó la petición") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="No se pudo contactar con el proveedor de IA") from exc

    try:
        data = response.json()
        content = data["choices"][0]["message"]["content"]
    except (KeyError, ValueError, AttributeError, IndexError, TypeError) as exc:
        raise HTTPException(status_code=502, detail="El proveedor devolvió una respuesta no válida") from exc

    if not isinstance(content, str) or not content.strip():
        raise HTTPException(status_code=502, detail="El proveedor devolvió una respuesta no válida")

    return SummarizeResponse(summary=content.strip())
