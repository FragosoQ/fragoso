"""Fragoso Bot — cérebro do assistente.

Substitui o app.py do Space Fragoso82/fragoso.

O que muda em relação à versão anterior:
  1. O endpoint expõe `history` e `system_prompt`. Sem isso o bot esquecia a
     conversa a cada mensagem e ignorava a personalidade definida na app.
  2. O parâmetro de texto passa a chamar-se `message` (antes `mensagem`), que
     era a origem do erro "No value provided for required parameter: mensagem".
  3. Se o modelo configurado não estiver disponível, tenta os alternativos em
     vez de falhar.

Configuração no Space (Settings):
  - Secrets   -> HF_TOKEN = token de leitura (obrigatório)
  - Variables -> MODELO   = modelos a tentar, separados por vírgulas (opcional)
  - Variables -> PROMPT   = personalidade por omissão (opcional)
"""

import inspect
import os
import re

import gradio as gr
from huggingface_hub import InferenceClient

# O ZeroGPU exige pelo menos uma função decorada com @spaces.GPU, senão o Space
# recusa arrancar. A inferência é remota e não usa GPU, por isso fica um esboço.
# O try/except mantém o ficheiro válido em hardware CPU, onde `spaces` não existe.
try:
    import spaces

    @spaces.GPU(duration=1)
    def _validacao_zerogpu():
        return "ok"

except Exception:
    pass


MODELOS_OMISSAO = [
    "Qwen/Qwen2.5-72B-Instruct",
    "meta-llama/Llama-3.3-70B-Instruct",
    "Qwen/Qwen2.5-Coder-32B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3",
]

MODELOS = [m.strip() for m in os.getenv("MODELO", "").split(",") if m.strip()] or MODELOS_OMISSAO
MAX_HISTORICO = 20           # mensagens enviadas ao modelo (limita custo e latência)
MAX_TOKENS_TETO = 8192       # teto absoluto, mesmo que a app peça mais
ORCAMENTO_RACIOCINIO = 2048  # tokens extra dados aos modelos que "pensam" antes

# Modelos oferecidos na app. A chave vazia significa "escolha automática".
CATALOGO = [
    ("", "Automático — rápido"),
    ("Qwen/Qwen2.5-72B-Instruct", "Qwen 2.5 72B — equilibrado"),
    ("meta-llama/Llama-3.3-70B-Instruct", "Llama 3.3 70B — conversa"),
    ("deepseek-ai/DeepSeek-R1", "DeepSeek R1 — raciocínio (lento)"),
]


def eh_modelo_raciocinio(modelo):
    """R1, QwQ e afins escrevem o raciocínio antes da resposta."""
    return bool(re.search(r"(^|[-/_])(r1|qwq|thinking|reasoner?)([-/_]|$)", str(modelo), re.I))


def limpar_raciocinio(texto):
    """Remove os blocos <think>…</think>: são notas internas do modelo.

    Sem isto o utilizador via — e o sintetizador lia em voz alta — todo o
    monólogo de raciocínio antes da resposta propriamente dita.
    """
    t = re.sub(r"<think>.*?</think>", "", texto, flags=re.S | re.I)
    # Bloco por fechar = ficou sem tokens a meio do raciocínio.
    t = re.sub(r"<think>.*$", "", t, flags=re.S | re.I)
    return t.strip()

PROMPT_OMISSAO = os.getenv(
    "PROMPT",
    "Tu és a extensão digital do Fragoso: inteligente, direto ao ponto, "
    "bem-humorado, levemente irónico e extremamente prático. Falas português "
    "de Portugal. Resolve o problema primeiro, sem enrolação nem desculpas "
    "desnecessárias. Respostas curtas salvo pedido em contrário.",
)

HF_TOKEN = os.getenv("HF_TOKEN")
cliente = InferenceClient(api_key=HF_TOKEN) if HF_TOKEN else None

# Primeiro modelo que respondeu — evita repetir tentativas falhadas.
_modelo_bom = None


def normalizar_historico(history):
    """Aceita os dois formatos: [{'role','content'}] e pares [utilizador, bot]."""
    saida = []
    for m in (history or []):
        if isinstance(m, dict) and m.get("role") in ("user", "assistant"):
            conteudo = m.get("content")
            if isinstance(conteudo, str) and conteudo.strip():
                saida.append({"role": m["role"], "content": conteudo})
        elif isinstance(m, (list, tuple)) and len(m) == 2:
            if m[0]:
                saida.append({"role": "user", "content": str(m[0])})
            if m[1]:
                saida.append({"role": "assistant", "content": str(m[1])})
    return saida[-MAX_HISTORICO:]


def responder(message, history=None, system_prompt=None, temperatura=0.7, max_tokens=1024, modelo=None):
    """Uma volta da conversa. É esta função que a app do browser chama."""
    global _modelo_bom

    if not message or not str(message).strip():
        return "Não recebi nenhuma pergunta."

    if cliente is None:
        return (
            "Falta o token. No Space: Settings -> Variables and secrets -> "
            "New secret, nome HF_TOKEN, valor do token criado em "
            "huggingface.co/settings/tokens (permissão de leitura)."
        )

    escolhido = (modelo or "").strip()
    raciocinio = eh_modelo_raciocinio(escolhido)
    persona = (system_prompt or PROMPT_OMISSAO).strip()
    pergunta = str(message).strip()

    if raciocinio:
        # A documentação do R1 desaconselha system prompt: as instruções devem
        # vir dentro da mensagem do utilizador.
        mensagens = normalizar_historico(history)
        mensagens.append({"role": "user", "content": f"{persona}\n\n---\n\n{pergunta}"})
    else:
        mensagens = [{"role": "system", "content": persona}]
        mensagens.extend(normalizar_historico(history))
        mensagens.append({"role": "user", "content": pergunta})

    # Modelo explícito da app; senão, o que já funcionou, senão a lista.
    if escolhido:
        candidatos = [escolhido]
    else:
        candidatos = ([_modelo_bom] if _modelo_bom else []) + [m for m in MODELOS if m != _modelo_bom]
    ultimo_erro = None

    # Limite pedido pela app, dentro de um intervalo sensato.
    limite = max(64, min(int(max_tokens or 1024), MAX_TOKENS_TETO))

    # O raciocínio também gasta tokens: sem folga extra, o modelo pensa até ao
    # limite e devolve resposta vazia.
    limite_envio = min(limite + ORCAMENTO_RACIOCINIO, MAX_TOKENS_TETO) if raciocinio else limite

    # O R1 fica incoerente fora de 0.5–0.7.
    temp = float(temperatura or 0.7)
    if raciocinio:
        temp = min(max(temp, 0.5), 0.7)

    for modelo_id in candidatos:
        try:
            resposta = cliente.chat_completion(
                messages=mensagens,
                model=modelo_id,
                max_tokens=limite_envio,
                temperature=temp,
            )
            escolha = resposta.choices[0]
            texto = (escolha.message.content or "").strip()

            if raciocinio:
                texto = limpar_raciocinio(texto)
                if not texto:
                    return (
                        "O modelo gastou todo o orçamento a raciocinar e não chegou a "
                        "responder. Suba o \"Comprimento máximo da resposta\" nos Ajustes, "
                        "ou escolha um modelo sem raciocínio."
                    )

            if texto:
                _modelo_bom = modelo_id
                # finish_reason="length" = ficou a meio por falta de tokens.
                if getattr(escolha, "finish_reason", None) == "length" and not raciocinio:
                    texto += (
                        "\n\n[Resposta cortada no limite de "
                        f"{limite} tokens. Aumente o \"Comprimento máximo da resposta\" nos Ajustes.]"
                    )
                return texto
            ultimo_erro = Exception("resposta vazia")
        except Exception as err:
            ultimo_erro = err
            # Erros de conta (token, créditos) não melhoram com outro modelo.
            if any(c in str(err) for c in ("401", "402")):
                break

    return traduzir_erro(ultimo_erro)


def traduzir_erro(err):
    """Erros crus de API não ajudam ninguém — dizer o que fazer."""
    msg = str(err)
    baixo = msg.lower()
    if "401" in msg or "unauthor" in baixo or ("invalid" in baixo and "token" in baixo):
        return "Token inválido ou sem permissões. Gere outro em huggingface.co/settings/tokens e atualize o secret HF_TOKEN."
    if "402" in msg or "quota" in baixo or "credit" in baixo or "payment" in baixo:
        return "Créditos de inferência esgotados este mês. Renovam no início do mês seguinte."
    if "403" in msg or "gated" in baixo:
        return "Os modelos configurados são restritos. Aceite as condições na página do modelo, ou mude a variável MODELO."
    if "404" in msg or "not found" in baixo:
        return f"Nenhum dos modelos está disponível para inferência ({', '.join(MODELOS[:3])}…). Mude a variável MODELO no Space."
    if "503" in msg or "loading" in baixo:
        return "O modelo está a arrancar. Tente daqui a 30 segundos."
    if "timeout" in baixo or "timed out" in baixo:
        return "O modelo demorou demasiado a responder. Tente outra vez."
    return f"Erro ao contactar o modelo: {msg[:200]}"


# --- Interface para pessoas (testar o Space no browser) --------------------

def _enviar_ui(mensagem, historico, prompt, temp, tokens, modelo):
    historico = historico or []
    if not (mensagem or "").strip():
        return historico, ""
    resposta = responder(mensagem, historico, prompt, temp, tokens, modelo)
    historico = historico + [
        {"role": "user", "content": mensagem},
        {"role": "assistant", "content": resposta},
    ]
    return historico, ""


def _kwargs_formato_mensagens(componente):
    """O Gradio 5 exige type="messages"; o 6 já usa esse formato e removeu o argumento."""
    return {"type": "messages"} if "type" in inspect.signature(componente.__init__).parameters else {}


with gr.Blocks(title="Fragoso Bot") as demo:
    gr.Markdown(
        "# Fragoso Bot\n"
        "Cérebro do assistente. Esta página serve para testar — "
        "a app do browser liga-se ao endpoint `/chat`."
    )

    conversa = gr.Chatbot(height=420, label="Conversa", **_kwargs_formato_mensagens(gr.Chatbot))
    caixa = gr.Textbox(placeholder="Escreva e carregue Enter…", label="Mensagem", lines=2)

    with gr.Accordion("Definições", open=False):
        prompt_ui = gr.Textbox(value=PROMPT_OMISSAO, label="Personalidade", lines=4)
        temp_ui = gr.Slider(0.1, 1.5, value=0.7, step=0.1, label="Temperatura")
        tokens_ui = gr.Slider(64, 8192, value=1024, step=64, label="Máximo de tokens")
        modelo_ui = gr.Dropdown(
            choices=[(rotulo, ident) for ident, rotulo in CATALOGO],
            value="", label="Modelo",
        )

    with gr.Row():
        enviar = gr.Button("Enviar", variant="primary")
        limpar = gr.Button("Limpar")

    entradas = [caixa, conversa, prompt_ui, temp_ui, tokens_ui, modelo_ui]
    saidas = [conversa, caixa]

    # api_name=False: pertencem à interface humana, não à API pública.
    caixa.submit(_enviar_ui, entradas, saidas, api_name=False)
    enviar.click(_enviar_ui, entradas, saidas, api_name=False)
    limpar.click(lambda: ([], ""), None, saidas, api_name=False)

    # --- Endpoint da API: é este que a app do browser chama -----------------
    # Componentes escondidos só para declarar a assinatura pública.
    api_message = gr.Textbox(visible=False, label="message")
    api_history = gr.JSON(visible=False, label="history", value=[])
    api_system = gr.Textbox(visible=False, label="system_prompt", value=PROMPT_OMISSAO)
    api_temp = gr.Number(visible=False, label="temperatura", value=0.7)
    api_tokens = gr.Number(visible=False, label="max_tokens", value=1024)
    api_modelo = gr.Textbox(visible=False, label="modelo", value="")
    api_saida = gr.Textbox(visible=False, label="resposta")
    api_botao = gr.Button(visible=False)

    api_botao.click(
        responder,
        [api_message, api_history, api_system, api_temp, api_tokens, api_modelo],
        api_saida,
        api_name="chat",
    )

if __name__ == "__main__":
    demo.launch()
