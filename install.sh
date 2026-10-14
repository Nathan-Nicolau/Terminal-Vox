#!/usr/bin/env bash
# ==============================================================================
# TerminalVox - Instalador Universal para Distribuições Linux
# Suporta: Ubuntu/Debian, Fedora, Arch Linux, openSUSE, etc.
# ==============================================================================

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "=================================================="
echo "🎙️  Instalador do TerminalVox"
echo "=================================================="

# 1. Detectar Distribuição Linux
DISTRO=""
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO="$ID"
    DISTRO_LIKE="$ID_LIKE"
fi

echo "[*] Distribuição detectada: $NAME ($DISTRO)"

# 2. Instalar Pacotes de Sistema
install_packages() {
    echo "[*] Instalando dependências do sistema..."
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update
        sudo apt-get install -y git build-essential cmake curl libnotify-bin ffmpeg \
            wl-clipboard ydotool xclip xdotool || true
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y git gcc gcc-c++ make cmake curl libnotify ffmpeg \
            wl-clipboard ydotool xclip xdotool || true
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -Sy --noconfirm git base-devel cmake curl libnotify ffmpeg \
            wl-clipboard ydotool xclip xdotool || true
    elif command -v zypper >/dev/null 2>&1; then
        sudo zypper install -y git gcc gcc-c++ make cmake curl libnotify-tools ffmpeg \
            wl-clipboard ydotool xclip xdotool || true
    else
        echo "[!] Gerenciador de pacotes não reconhecido automaticamente."
        echo "    Certifique-se de ter instalado: git, make, cmake, gcc/g++, ffmpeg, wl-clipboard/xclip, ydotool/xdotool."
    fi
}

install_packages

# 3. Configurar permissões de teclado virtual (para Wayland / ydotool)
if [ "$XDG_SESSION_TYPE" = "wayland" ] || command -v ydotool >/dev/null 2>&1; then
    echo "[*] Configurando permissões do kernel para /dev/uinput (Wayland)..."
    if [ ! -f /etc/udev/rules.d/99-uinput.rules ]; then
        echo 'KERNEL=="uinput", GROUP="input", MODE="0660"' | sudo tee /etc/udev/rules.d/99-uinput.rules >/dev/null
    fi
    sudo usermod -aG input "$USER" 2>/dev/null || true
    sudo chmod 666 /dev/uinput 2>/dev/null || true
fi

# 4. Clonar e Compilar whisper.cpp se necessário
if [ ! -f "$DIR/whisper.cpp/build/bin/whisper-cli" ]; then
    echo "[*] Preparando whisper.cpp..."
    if [ ! -d "$DIR/whisper.cpp" ]; then
        git clone --depth 1 https://github.com/ggerganov/whisper.cpp.git "$DIR/whisper.cpp"
    fi
    echo "[*] Compilando whisper.cpp com otimizações de CPU..."
    cd "$DIR/whisper.cpp"
    cmake -B build -DWHISPER_BUILD_EXAMPLES=ON
    cmake --build build --config Release -j"$(nproc)"
    cd "$DIR"
fi

# 5. Baixar modelo base se não existir
if [ ! -f "$DIR/whisper.cpp/models/ggml-base.bin" ]; then
    echo "[*] Baixando modelo base do Whisper (~140 MB)..."
    cd "$DIR/whisper.cpp"
    bash models/download-ggml-model.sh base
    cd "$DIR"
fi

# 6. Permissões de Execução
chmod +x "$DIR/voice_toggle.sh" "$DIR/voice_master_switch.sh" "$DIR/record_and_transcribe.py"

echo "=================================================="
echo "✅ Instalação concluída com sucesso!"
echo "=================================================="
echo ""
echo "📌 Para usar em qualquer ambiente desktop (GNOME, KDE, XFCE, Hyprland, i3, etc.):"
echo ""
echo "1. Atalho 1 (Chave Geral - Ligar/Desligar modo de voz):"
echo "   Comando: $DIR/voice_master_switch.sh"
echo "   Sugestão de tecla: Super+Alt+V ou F7"
echo ""
echo "2. Atalho 2 (Gravar e Injetar no Terminal):"
echo "   Comando: $DIR/voice_toggle.sh"
echo "   Sugestão de tecla: F8 ou Pause"
echo ""
