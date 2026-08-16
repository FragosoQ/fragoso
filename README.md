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

## API própria (FastAPI)

**A API só é precisa no modo "FastAPI / Servidor Customizado".** Nos modos *Demo Local* e *Hugging Face Space* não é preciso servidor nenhum — se vir erros de ligação, confirme primeiro qual a origem escolhida nos Ajustes.

**Windows:** duplo-clique em `iniciar-api.bat`. Procura o Python, instala as dependências e arranca o servidor. Deixar a janela aberta enquanto usa a app.

O `server.py` incluído é um esqueleto funcional. Arrancar à mão:

```bash
pip install -r requirements.txt
python -m uvicorn server:app --port 8000 --reload
```

No Windows, se `python` não for reconhecido, usar `py -m uvicorn server:app --port 8000 --reload`.

Confirmar em `http://localhost:8000/health` — deve devolver `{"status":"ok"}`.

Nos **Ajustes → FastAPI / Servidor Customizado** há um botão **Testar a API** que diz exatamente onde está o problema: servidor em baixo, rota errada, resposta sem o campo `response`, ou bloqueio por HTTPS/HTTP.

Abrir a raiz (`http://localhost:8000/`) mostra uma página de estado com o URL exato a colar nos Ajustes. `/docs` dá a documentação interativa.

### GitHub Codespaces

Num Codespace o servidor **não está no seu computador**, por isso `localhost:8000` no browser não lhe chega.

**O `--host` é obrigatório.** Sem ele o uvicorn liga-se só a `127.0.0.1`, fica visível apenas dentro do contentor, e o separador **PORTS** mostra *"No forwarded ports"*:

```bash
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

Ou simplesmente `./iniciar-api.sh`, que já faz isso.

Depois:

1. A porta 8000 aparece no separador **PORTS**.
2. Botão direito na porta → **Port Visibility → Public**. Sem isto o browser recebe a página de login do GitHub em vez da resposta da API, e o erro aparece disfarçado de CORS.
3. Copiar o endereço reencaminhado e usar **`https://<codespace>-8000.app.github.dev/api/chat`** nos Ajustes.

O `.devcontainer/devcontainer.json` incluído reencaminha as portas 8000 e 8080 automaticamente e instala as dependências ao criar o Codespace. Só produz efeito em Codespaces novos ou após **Rebuild Container**.

O `server.py` já autoriza `*.app.github.dev` e `*.github.io` por CORS. A app deteta a situação e avisa se o URL apontar para `localhost` estando a página num domínio remoto.

### Erros comuns

| Sintoma | Causa | Solução |
|---|---|---|
| `ERR_CONNECTION_REFUSED` / "Failed to fetch" | O `server.py` não está a correr | Arrancar o uvicorn (acima) |
| Funciona no Chrome, falha noutro browser | Página em HTTPS a chamar `http://` | Expor a API em HTTPS |
| `CORS policy` na consola | A origem da página não está autorizada | Ver abaixo |
| Resposta vazia no chat | O JSON não tem o campo `response` | Devolver `{"response": "..."}` |

O `server.py` já aceita **qualquer porta de `localhost`**, por isso serve o `python -m http.server 8080`, o Live Server (5500) ou o Vite (5173) sem configuração. Para o GitHub Pages, indicar a origem:

```bash
FRAGOSO_ORIGINS=https://utilizador.github.io python -m uvicorn server:app --port 8000
```

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

## Voz (TTS)

Mudar o **Idioma da Fala** não chega. A Web Speech API ignora `utterance.lang` na prática: se não for atribuída uma voz, o motor usa a voz por omissão do sistema — normalmente portuguesa — e lê o texto inglês com fonética portuguesa.

A app passou a escolher explicitamente uma `SpeechSynthesisVoice` do idioma pedido. Em **Ajustes → Controles de Voz**:

- **Voz** — lista as vozes que o sistema tem para o idioma escolhido. Em "Automática" prefere vozes locais (não dependem de rede).
- **Ouvir amostra** — testa com uma frase no idioma selecionado, sem obrigar a guardar.

Se o seletor disser *"nenhuma voz para xx-XX"*, o sistema operativo não tem essa voz instalada:

- **Windows** — Definições → Hora e Idioma → Voz → Adicionar vozes.
- **Android/iOS** — definições de acessibilidade / conversão de texto em voz.
- **Chrome no computador** — algumas vozes Google só existem online.

O idioma também é aplicado ao reconhecimento de voz (microfone).

## Modo conversa (mãos livres)

Três formas de entrar: o botão **Conversa** no cabeçalho, o botão grande no ecrã de boas-vindas, ou o auricular ao lado do microfone.

Abre um ecrã dedicado com **visualizador de áudio em tempo real** — as barras reagem ao nível do microfone através da Web Audio API (`AnalyserNode`), não é animação decorativa. As cores seguem o estado: verde a ouvir, âmbar a pensar, azul a responder. Uma linha na base mostra o avanço da pausa, ou seja, quanto falta para a frase ser enviada.

Enquanto o bot fala o microfone está fechado, por isso nesse período a onda é sintética — não há áudio de entrada para medir.

Depois de iniciado não é preciso carregar em mais nada:

1. A app ouve em contínuo e mostra em tempo real o que vai transcrevendo.
2. Ao detetar **1,5 s de silêncio** conclui que a frase acabou e envia.
3. Enquanto o bot fala, o microfone fecha — evita que ele se ouça a si próprio e entre em ciclo.
4. Assim que se cala, o microfone reabre sozinho.
5. Dizer **"até amanhã"** (ou "adeus") termina a conversa e o bot despede-se.

O ecrã mostra a transcrição em direto enquanto fala, o que foi efetivamente captado quando envia, e um resumo da resposta do bot.

O visualizador usa um segundo acesso ao microfone, independente do reconhecimento de voz. Se esse acesso for recusado, o modo conversa continua a funcionar — apenas a onda passa a aproximada, com aviso no ecrã.

Nos **Ajustes → Controles de Voz**:

- **Pausa que conclui a frase** — 0,6 s a 4 s. Subir se costumar fazer pausas a pensar a meio da frase.
- **Frases que terminam a conversa** — lista separada por vírgulas. Acentos, maiúsculas e pequenos erros de transcrição são tolerados (*"atá amamhã"* também termina).

O modo conversa liga a leitura das respostas enquanto está ativo, sem alterar a preferência guardada. Requer Chrome ou Edge, e HTTPS (ou `localhost`) para aceder ao microfone.

**Auscultadores são recomendados.** Com o altifalante do portátil, o microfone só reabre depois de o bot terminar — por isso não há eco, mas também não é possível interrompê-lo a meio.

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
| `iniciar-api.bat` | Arranca a API no Windows com duplo-clique |
| `iniciar-api.sh` | Arranca a API no Linux/macOS/Codespaces (com `--host 0.0.0.0`) |
| `.devcontainer/` | Reencaminha as portas 8000 e 8080 no Codespaces |
| `requirements.txt` | Dependências Python da API |
| `.nojekyll` | Impede o GitHub Pages de processar os ficheiros com Jekyll |
| `.gitignore` | Exclui modelos, ambientes virtuais e ficheiros de sistema |
