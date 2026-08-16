"""API mínima para o Fragoso Bot (provider "FastAPI / Servidor Customizado").

Correr:  uvicorn server:app --host 0.0.0.0 --port 8000 --reload
"""

import os
from typing import List, Literal, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="Fragoso Bot API")

# Origens autorizadas.
#   - Qualquer porta de localhost é aceite (o servidor estático muda de porta
#     conforme a ferramenta: 8080, 5500 do Live Server, 5173 do Vite...).
#   - Para o GitHub Pages, acrescentar a origem em FRAGOSO_ORIGINS:
#       FRAGOSO_ORIGINS=https://utilizador.github.io python -m uvicorn server:app
# Nunca usar "*" com allow_credentials=True: o browser rejeita a combinação.
LOCALHOST_REGEX = r"^https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$"

ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv("FRAGOSO_ORIGINS", "").split(",") if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=os.getenv("FRAGOSO_ORIGIN_REGEX", LOCALHOST_REGEX),
    allow_credentials=False,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    # O front-end envia sempre os três campos.
    message: str
    history: List[Message] = Field(default_factory=list)
    system_prompt: Optional[str] = None


class ChatResponse(BaseModel):
    response: str


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest) -> ChatResponse:
    user_msg = req.message.strip()
    if not user_msg:
        return ChatResponse(response="Mensagem vazia.")

    # TODO: ligar aqui o modelo. `req.history` e `req.system_prompt` já vêm prontos.
    return ChatResponse(
        response=f"Recebido no servidor! Disseste: '{user_msg}' "
                 f"({len(req.history)} mensagens de histórico)"
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
