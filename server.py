from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI()

# Configuração de CORS permissiva para o GitHub Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

# Responde aos testes automáticos que o navegador faz antes de enviar a mensagem
@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    response = Response(status_code=200)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    user_msg = req.message.strip()
    
    # Resposta apenas em texto
    bot_response = f"Recebido! Disseste: '{user_msg}'"

    return JSONResponse(
        content={"response": bot_response},
        headers={"Access-Control-Allow-Origin": "*"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)