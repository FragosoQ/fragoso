---
title: Fragoso Bot
emoji: 🤖
colorFrom: indigo
colorTo: purple
sdk: gradio
sdk_version: 5.49.1
app_file: app.py
pinned: false
short_description: Cérebro do assistente Fragoso Bot
---

# Fragoso Bot — cérebro

Space que serve de motor ao [Fragoso Bot](https://fragosoq.github.io). O Space não
executa o modelo: chama um modelo alojado através da Inference API da Hugging
Face. Corre no hardware **CPU basic (gratuito)** e a chave nunca fica exposta
no browser.

## Configurar (obrigatório)

Sem isto o Space responde a dizer que falta o token.

1. Criar um token em **huggingface.co/settings/tokens** → *Create new token* →
   tipo **Read**.
2. Neste Space: **Settings → Variables and secrets → New secret**
   - Name: `HF_TOKEN`
   - Value: o token copiado
3. O Space reinicia sozinho. Esperar ~1 minuto.

## Opcional

Em **Settings → Variables** (variáveis, não secrets):

| Variável | Para quê | Omissão |
|---|---|---|
| `MODELO` | Trocar de modelo | `Qwen/Qwen2.5-7B-Instruct` |
| `PROMPT` | Personalidade base | Perfil "Fragoso" |

Se o modelo por omissão der erro 404 ou 403, experimentar outro que esteja
disponível para inferência — por exemplo `meta-llama/Llama-3.1-8B-Instruct`
(exige aceitar as condições na página do modelo) ou
`mistralai/Mistral-7B-Instruct-v0.3`.

## Ligar a app

Na app, **Ajustes → Origem do Chatbot → Hugging Face Space**:

- **Nome do Space**: `utilizador/fragoso-bot`
- **Endpoint**: deixar vazio (a app deteta `/chat` sozinha)

O botão **Testar ligação e ver parâmetros** confirma tudo antes de fechar.

## API

Endpoint `/chat`:

| Parâmetro | Tipo | Obrigatório |
|---|---|---|
| `message` | str | sim |
| `history` | lista de `{role, content}` | não |
| `system_prompt` | str | não |
| `temperatura` | float | não |
| `max_tokens` | float | não |

O `history` é explícito de propósito: sem ele a conversa perdia a memória a
cada mensagem, porque cada chamada à API é independente.
