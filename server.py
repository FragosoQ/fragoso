from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import edge_tts
import os

app = FastAPI()

# Permite chamadas de qualquer origem sem restrições
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

# Rota para responder a pedidos de verificação do navegador (Preflight)
@app.options("/{full_path:path}")
async def options_handler():
    return Response(status_code=200)

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest, request: Request):
    user_msg = req.message.strip()
    
    bot_response = f"Olá! Recebi a tua mensagem: '{user_msg}'"

    os.makedirs("static", exist_ok=True)
    output_audio = "static/vader_response.mp3"
    
    communicate = edge_tts.Communicate(bot_response, voice="pt-PT-DuarteNeural")
    await communicate.save(output_audio)
    
    base_url = str(request.base_url).rstrip("/")
    if base_url.startswith("http://"):
        base_url = base_url.replace("http://", "https://", 1)
        
    audio_url = f"{base_url}/audio"
    
    return JSONResponse(content={
        "response": bot_response,
        "audio_url": audio_url
    })

@app.get("/audio")
async def get_audio():
    return FileResponse("static/vader_response.mp3", media_type="audio/mpeg")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)