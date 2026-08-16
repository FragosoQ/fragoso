#!/usr/bin/env bash
# Arranca a API do Fragoso Bot no Linux / macOS / GitHub Codespaces.
#   ./iniciar-api.sh
#
# O --host 0.0.0.0 é essencial no Codespaces: preso a 127.0.0.1 o servidor
# só é visível dentro do contentor e a porta nunca aparece no separador PORTS.

set -euo pipefail
cd "$(dirname "$0")"

PY="${PYTHON:-python3}"
command -v "$PY" >/dev/null 2>&1 || PY=python
command -v "$PY" >/dev/null 2>&1 || { echo "Python não encontrado."; exit 1; }

PORTA="${PORTA:-8000}"

echo "A verificar dependências..."
"$PY" -m pip install --quiet --disable-pip-version-check -r requirements.txt

echo
echo "============================================"
echo " API a arrancar na porta $PORTA (host 0.0.0.0)"
echo
echo " Codespaces: a porta $PORTA aparece no separador PORTS."
echo "   1. Botão direito -> Port Visibility -> Public"
echo "   2. Copiar o endereço e usar <endereco>/api/chat nos Ajustes"
echo
echo " Local: http://localhost:$PORTA"
echo "============================================"
echo

exec "$PY" -m uvicorn server:app --host 0.0.0.0 --port "$PORTA" --reload
