#!/usr/bin/env bash
# Atalho de gravação de voz para o agente - TerminalVox
# Se o modo de voz estiver desativado, o atalho não faz nada.
ENABLED_FLAG="$HOME/.config/terminalvox/enabled"
if [ ! -f "$ENABLED_FLAG" ]; then
    exit 0
fi

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Se houver display gráfico ativo, abre o HUD moderno com ondas de áudio e status
if [ -n "$WAYLAND_DISPLAY" ] || [ -n "$DISPLAY" ]; then
    exec python3 "$DIR/terminalvox_hud.py"
else
    # Fallback para ambiente puramente headless/SSH
    exec python3 "$DIR/record_and_transcribe.py" --toggle
fi
