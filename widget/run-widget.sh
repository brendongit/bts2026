#!/usr/bin/env bash
# Abre o widget (hospedado na Vercel) como uma janela fixa do Chrome
# (sem abas/barra de endereço), num perfil próprio (não mexe no seu Chrome normal).
set -euo pipefail

WIDGET_URL="https://bts2026-gamma.vercel.app/widget/widget.html"
PROFILE_DIR="$HOME/.config/bts-widget-chrome"

# tamanho e posição da janela — ajuste aqui se quiser mudar o canto
WIDTH=280
HEIGHT=250
# padrão: canto inferior direito de uma tela 1920x1080 com margem de 20px
POS_X=${POS_X:-1640}
POS_Y=${POS_Y:-800}

if pgrep -f "user-data-dir=$PROFILE_DIR" > /dev/null; then
  echo "Widget já está rodando (profile $PROFILE_DIR). Não abri outra janela."
  exit 0
fi

mkdir -p "$PROFILE_DIR"

google-chrome \
  --app="$WIDGET_URL" \
  --user-data-dir="$PROFILE_DIR" \
  --window-size=${WIDTH},${HEIGHT} \
  --window-position=${POS_X},${POS_Y} \
  --no-first-run \
  --no-default-browser-check \
  >/tmp/bts-widget.log 2>&1 &
disown

echo "Widget lançado (pid $!). Se não aparecer no canto certo, arraste a janela manualmente —"
echo "a posição vai ficar salva pro Chrome usar da próxima vez (esse profile é só do widget)."

# deixa a janela "sempre no topo" (precisa do wmctrl: sudo apt install wmctrl)
if command -v wmctrl > /dev/null; then
  for i in $(seq 1 20); do
    if wmctrl -l | grep -q "BTS Arirang - Widget"; then
      wmctrl -r "BTS Arirang - Widget" -b add,above
      echo "Janela marcada como 'sempre no topo'."
      break
    fi
    sleep 0.5
  done
else
  echo "wmctrl não instalado — pulei o 'sempre no topo' (sudo apt install wmctrl pra habilitar)."
fi
