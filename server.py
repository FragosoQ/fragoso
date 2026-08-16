"""API mínima para o Fragoso Bot (provider "FastAPI / Servidor Customizado").

Correr:  uvicorn server:app --host 0.0.0.0 --port 8000 --reload
"""

import os
from typing import List, Literal, Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

app = FastAPI(title="Fragoso Bot API")

# Origens autorizadas. Aceita por omissão:
#   - qualquer porta de localhost (http.server 8080, Live Server 5500, Vite 5173...);
#   - portas reencaminhadas do GitHub Codespaces (*.app.github.dev);
#   - GitHub Pages (*.github.io).
# Para outra origem, usar FRAGOSO_ORIGINS (lista separada por vírgulas).
# Nunca usar "*" com allow_credentials=True: o browser rejeita a combinação.
ORIGENS_REGEX = (
    r"^https?://("
    r"localhost|127\.0\.0\.1|\[::1\]"            # desenvolvimento local
    r")(:\d+)?$"
    r"|^https://[a-z0-9-]+\.app\.github\.dev$"    # GitHub Codespaces
    r"|^https://[a-z0-9-]+\.github\.io$"          # GitHub Pages
)

ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv("FRAGOSO_ORIGINS", "").split(",") if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=os.getenv("FRAGOSO_ORIGIN_REGEX", ORIGENS_REGEX),
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


@app.get("/", response_class=HTMLResponse)
async def raiz(request: Request):
    """Página de estado.

    Sem isto, abrir a raiz devolve {"detail":"Not Found"} e parece que
    o servidor está avariado — quando na verdade só não tem rota em "/".
    """
    base = str(request.base_url).rstrip("/")
    return f"""<!DOCTYPE html>
<html lang="pt-PT"><head><meta charset="utf-8">
<title>Fragoso Bot — API</title>
<style>
 body{{font-family:system-ui,sans-serif;background:#020617;color:#e2e8f0;
      display:flex;min-height:100vh;align-items:center;justify-content:center;margin:0;padding:24px}}
 .c{{max-width:620px;width:100%}}
 h1{{margin:0 0 4px;font-size:20px}} p{{color:#94a3b8;font-size:14px;line-height:1.6}}
 code{{background:#0f172a;border:1px solid #1e293b;border-radius:6px;padding:2px 6px;
      font-size:13px;color:#a5b4fc;word-break:break-all}}
 .ok{{display:inline-flex;align-items:center;gap:8px;background:#022c22;color:#6ee7b7;
      border:1px solid #065f46;border-radius:999px;padding:4px 12px;font-size:13px;margin-bottom:16px}}
 table{{width:100%;border-collapse:collapse;margin:16px 0;font-size:13px}}
 td{{padding:8px 10px;border-bottom:1px solid #1e293b;vertical-align:top}}
 td:first-child{{color:#a5b4fc;font-family:ui-monospace,monospace;white-space:nowrap}}
 .box{{background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:14px;margin-top:16px}}
</style></head><body><div class="c">
<div class="ok">● API a funcionar</div>
<h1>Fragoso Bot — API</h1>
<p>Esta página confirma que o servidor arrancou. Ela própria não faz nada:
a app fala com os endpoints abaixo.</p>
<table>
  <tr><td>GET /health</td><td>Verificação rápida do estado</td></tr>
  <tr><td>POST /api/chat</td><td>Endpoint do chat</td></tr>
  <tr><td>GET /docs</td><td>Documentação interativa (Swagger)</td></tr>
</table>
<div class="box">
<p style="margin:0 0 8px;color:#e2e8f0"><strong>Cole este URL nos Ajustes da app:</strong></p>
<code>{base}/api/chat</code>
</div>
<p style="margin-top:16px;font-size:13px">
Se estiver no GitHub Codespaces, confirme no separador <strong>PORTS</strong> que a
porta 8000 tem visibilidade <strong>Public</strong> — caso contrário o browser
recebe a página de login do GitHub em vez da resposta da API.</p>
</div></body></html>"""


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
