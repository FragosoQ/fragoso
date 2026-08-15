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

## Ligar a um Hugging Face Space

Cada Space declara os seus próprios nomes de parâmetros — pode ser `message`, `mensagem`, `pergunta`, `prompt`. A app já **lê a assinatura do Space** (`view_api()`) e preenche os argumentos com os nomes reais, por isso não é preciso adivinhar.

Se mesmo assim falhar, abrir **Ajustes → Testar ligação e ver parâmetros**. Mostra:

- os endpoints disponíveis;
- qual está a ser usado;
- os nomes e tipos dos parâmetros (`*` = obrigatório).

Com essa informação, escrever o endpoint correto no campo **Endpoint da API do Space**.

## Imagens

Escrever `/imagem <descrição>` na conversa, ou carregar no botão da imagem ao lado do enviar.

As imagens são geradas por um **Space** com Gradio, não pela API de inferência paga. Isso usa a quota diária de GPU das Spaces, que é gratuita. Nos Ajustes:

- **Space que gera as imagens** — por exemplo `black-forest-labs/FLUX.1-schnell`.
- **Endpoint** — em branco deteta sozinho; costuma ser `/infer`.
- **Token do Hugging Face** — opcional. Sem token funciona com menos quota diária.

Vale a pena **duplicar** o Space para a conta própria (botão *Duplicate this Space* na página do Space): fica sempre disponível, sem fila partilhada, e consome a quota própria.

As imagens ficam só na sessão — usar o botão de descarregar para guardar.

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

**Os ícones são obrigatórios para instalar.** A pasta `icons/` tem de conter `icon-192.png`, `icon-512.png`, `maskable-192.png`, `maskable-512.png`, `apple-touch-icon.png` e `favicon-64.png`. Sem eles o Chrome não mostra o botão **Instalar**. O service worker já tolera a ausência (não aborta a instalação), mas o PWA não fica instalável.

## Modelos de voz (fase 2)

`models/` e os ficheiros `*.pth` / `*.index` estão no `.gitignore` — **não vão para o GitHub**. É intencional:

- o GitHub bloqueia ficheiros acima de 100 MB (um `.index` de RVC passa disso com frequência);
- o GitHub Pages serve ficheiros estáticos, não executa modelos.

Um modelo RVC não corre no browser. A inferência tem de ficar num **Space com GPU** ou numa API própria, e a app chama esse endpoint. Para versionar os pesos, usar Git LFS:

```bash
git lfs install
git lfs track "*.pth" "*.index"
git add .gitattributes
```

E remover as linhas correspondentes do `.gitignore`.

## Ficheiros

| Ficheiro | O que faz |
|---|---|
| `index.html` | A aplicação toda: interface, lógica e ligações |
| `manifest.webmanifest` | Nome, ícones, cores e modo de janela da app instalada |
| `sw.js` | Service worker: funcionamento offline e cache |
| `icons/` | Ícones 192/512, maskable, Apple touch e favicon |
| `server.py` | API FastAPI de exemplo para o modo "Servidor Customizado" |
| `.nojekyll` | Impede o GitHub Pages de processar os ficheiros com Jekyll |
| `.gitignore` | Exclui modelos, ambientes virtuais e ficheiros de sistema |
