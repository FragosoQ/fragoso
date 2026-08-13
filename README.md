# Fragoso Bot

Chatbot personalizado num único ficheiro HTML, instalável como PWA. Três origens de resposta, escolhidas nos Ajustes:

- **Demo local** — respostas simuladas, sem rede e sem chaves.
- **Hugging Face Space** — liga a um Space com Gradio.
- **API própria** — endpoint FastAPI (ou outro) que aceite `POST` com `{ message, history, system_prompt }`.

As configurações ficam no `localStorage` do browser. Não há servidor nem base de dados.

## Publicar no GitHub Pages

1. Criar um repositório novo no GitHub (público, sem README, sem `.gitignore`).
2. Fazer upload de **todo** o conteúdo desta pasta para a raiz do repositório — `index.html`, `sw.js`, `manifest.webmanifest`, `.nojekyll` e a pasta `icons/`.
3. No repositório, ir a **Settings → Pages**.
4. Em *Source*, escolher **Deploy from a branch**; em *Branch*, escolher `main` e a pasta `/ (root)`. Gravar.
5. Esperar 1–2 minutos. O endereço fica `https://<utilizador>.github.io/<repositório>/`.
6. Abrir esse endereço no Chrome do telemóvel e usar **Adicionar ao ecrã principal**. No computador aparece o botão **Instalar** no cabeçalho.

Todos os caminhos são relativos (`./`), por isso funciona num subdiretório sem alterações.

## Notas importantes

**HTTPS é obrigatório para o PWA.** O GitHub Pages já serve em HTTPS. Ao abrir o ficheiro directamente do disco (`file://`) o service worker não registra e não há instalação — para testar localmente, correr um servidor:

```bash
python3 -m http.server 8080
# depois abrir http://localhost:8080
```

**A API em `http://localhost` não funciona a partir do GitHub Pages.** Uma página em HTTPS não pode chamar um endereço em HTTP: o Chrome ainda abre uma exceção para `localhost`, mas o Firefox e o Safari bloqueiam. Opções:

- expor a API em HTTPS (Cloudflare Tunnel, ngrok, ou um domínio próprio);
- ou usar a versão local do ficheiro para falar com a API local.

**A API precisa de CORS.** Em FastAPI:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://<utilizador>.github.io"],
    allow_methods=["POST"],
    allow_headers=["*"],
)
```

**Cache do service worker.** Depois de alterar o `index.html`, incrementar `VERSION` no `sw.js` (`v1` → `v2`), senão os visitantes que já instalaram continuam a ver a versão antiga.

## Ficheiros

| Ficheiro | O que faz |
|---|---|
| `index.html` | A aplicação toda: interface, lógica e ligações |
| `manifest.webmanifest` | Nome, ícones, cores e modo de janela da app instalada |
| `sw.js` | Service worker: funcionamento offline e cache |
| `icons/` | Ícones 192/512, maskable, Apple touch e favicon |
| `.nojekyll` | Impede o GitHub Pages de processar os ficheiros com Jekyll |
