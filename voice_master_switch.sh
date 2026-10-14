#!/usr/bin/env bash
# Chave Geral (Ligar / Desligar Modo de Voz) - TerminalVox
CONFIG_DIR="$HOME/.config/terminalvox"
ENABLED_FLAG="$CONFIG_DIR/enabled"
PID_FILE="/tmp/voice_input_recording.pid"

mkdir -p "$CONFIG_DIR"

if [ -f "$ENABLED_FLAG" ]; then
    # Desativa
    rm -f "$ENABLED_FLAG"
    # Interrompe qualquer gravação pendente
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE" 2>/dev/null)
        [ -n "$PID" ] && kill -INT "$PID" 2>/dev/null
        rm -f "$PID_FILE"
    fi
    notify-send -a "TerminalVox" -i audio-volume-muted "🔇 TerminalVox DESATIVADO" "O microfone e o atalho de gravação estão desligados."
    echo "[*] TerminalVox DESATIVADO"
else
    # Ativa
    touch "$ENABLED_FLAG"
    notify-send -a "TerminalVox" -i audio-input-microphone "🎙️ TerminalVox ATIVADO" "O atalho de gravação está pronto para ser usado."
    echo "[*] TerminalVox ATIVADO"
fi
