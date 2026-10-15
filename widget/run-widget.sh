#!/usr/bin/env bash
# Abre o widget.html como uma janela fixa (sem abas/barra de endereço) do Chrome,
# num perfil próprio (não mexe no seu Chrome normal).
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HTML_PATH="$DIR/widget.html"
PROFILE_DIR="$HOME/.config/bts-widget-chrome"

# o Chrome exige o file:// URL com espaços/acentos escapados
FILE_URL="file://$(python3 -c "import sys, urllib.parse as u; print(u.quote(sys.argv[1]))" "$HTML_PATH")"

# tamanho e posição da janela — ajuste aqui se quiser mudar o canto
WIDTH=260
HEIGHT=210
# padrão: canto inferior direito de uma tela 1920x1080 com margem de 20px
POS_X=${POS_X:-1640}
POS_Y=${POS_Y:-800}

mkdir -p "$PROFILE_DIR"

google-chrome \
  --app="$FILE_URL" \
  --user-data-dir="$PROFILE_DIR" \
  --window-size=${WIDTH},${HEIGHT} \
  --window-position=${POS_X},${POS_Y} \
  --no-first-run \
  --no-default-browser-check \
  >/tmp/bts-widget.log 2>&1 &
disown

echo "Widget lançado (pid $!). Se não aparecer no canto certo, arraste a janela manualmente —"
echo "a posição vai ficar salva pro Chrome usar da próxima vez (esse profile é só do widget)."
