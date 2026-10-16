#!/usr/bin/env python3
"""
Terminal Voice Input - Transcrição local para agentes de IA
Ubuntu 24.04 (Wayland) + PipeWire + whisper.cpp
"""

import os
import sys
import time
import signal
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
WHISPER_BIN = BASE_DIR / "whisper.cpp" / "build" / "bin" / "whisper-cli"

# O modelo base é ~4x mais rápido que o small, e com o TECH_PROMPT mantém a precisão
MODEL_BASE = BASE_DIR / "whisper.cpp" / "models" / "ggml-base.bin"
MODEL_SMALL = BASE_DIR / "whisper.cpp" / "models" / "ggml-small.bin"
# Se VOICE_MODEL=small for definido no ambiente usa small, caso contrário usa base (alta velocidade)
use_small = os.environ.get("VOICE_MODEL", "").lower() == "small"
MODEL_PATH = MODEL_SMALL if (use_small and MODEL_SMALL.exists()) else MODEL_BASE

AUDIO_FILE = "/tmp/voice_input_recording.wav"
PID_FILE = "/tmp/voice_input_recording.pid"

# Chave Mestre de Ativação / Desativação
CONFIG_DIR = Path.home() / ".config" / "terminalvox"
ENABLED_FLAG = CONFIG_DIR / "enabled"

def is_voice_enabled() -> bool:
    return ENABLED_FLAG.exists()

# Contexto técnico para evitar que termos como 'branch', 'merge', 'build' sejam confundidos
TECH_PROMPT = "Comandos de terminal, código, git, branch, commit, merge, master, main, build, pull request, push, checkout, revert, deploy, release, bugs, testes, funções, Linux, Python, ESP32."


import shutil

def notify(title: str, message: str, icon: str = "dialog-information"):
    # As mensagens agora são exibidas visualmente no HUD (TerminalVox HUD).
    # Notificações do SO são reservadas exclusivamente para ativar/desativar a chave mestre.
    pass

def copy_to_clipboard(text: str) -> bool:
    # 1. Wayland (wl-copy)
    if shutil.which("wl-copy"):
        try:
            proc = subprocess.run(["wl-copy"], input=text, text=True, check=False)
            if proc.returncode == 0:
                return True
        except Exception:
            pass

    # 2. X11 (xclip)
    if shutil.which("xclip"):
        try:
            proc = subprocess.run(["xclip", "-selection", "clipboard"], input=text, text=True, check=False)
            if proc.returncode == 0:
                return True
        except Exception:
            pass

    # 3. X11 (xsel)
    if shutil.which("xsel"):
        try:
            proc = subprocess.run(["xsel", "--clipboard", "--input"], input=text, text=True, check=False)
            if proc.returncode == 0:
                return True
        except Exception:
            pass

    # 4. Fallback via GTK (GNOME / Cinnamon / XFCE)
    try:
        import gi
        gi.require_version('Gtk', '4.0')
        from gi.repository import Gdk
        display = Gdk.Display.get_default()
        if display:
            clipboard = display.get_clipboard()
            clipboard.set(text)
            return True
    except Exception:
        pass

    return False

def paste_to_terminal() -> bool:
    """Injeta Ctrl+Shift+V de acordo com o servidor gráfico (Wayland ou X11)."""
    time.sleep(0.2)  # Dá tempo do clipboard registrar o novo conteúdo
    session = os.environ.get("XDG_SESSION_TYPE", "").lower()

    # 1. No Wayland: prioridade obrigatória para ydotool / wtype
    if session == "wayland":
        if shutil.which("ydotool"):
            try:
                proc = subprocess.run(["ydotool", "key", "ctrl+shift+v"], 
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
                if proc.returncode == 0:
                    return True
            except Exception:
                pass

        if shutil.which("wtype"):
            try:
                proc = subprocess.run(["wtype", "-M", "ctrl", "-M", "shift", "v"],
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
                if proc.returncode == 0:
                    return True
            except Exception:
                pass

    # 2. No X11: usa xdotool nativo
    else:
        if shutil.which("xdotool"):
            try:
                proc = subprocess.run(["xdotool", "key", "ctrl+shift+v"],
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
                if proc.returncode == 0:
                    return True
            except Exception:
                pass

    return False

def get_audio_recorder_cmd(audio_file: str):
    """Detecta automaticamente o gravador disponível (PipeWire, PulseAudio ou ALSA)."""
    if shutil.which("pw-record"):
        return ["pw-record", "--rate", "16000", "--channels", "1", audio_file]
    elif shutil.which("parec"):
        return ["parec", "--rate=16000", "--channels=1", "--file-format=wav", audio_file]
    elif shutil.which("ffmpeg"):
        return ["ffmpeg", "-y", "-loglevel", "error", "-f", "pulse", "-i", "default", "-ar", "16000", "-ac", "1", audio_file]
    elif shutil.which("arecord"):
        return ["arecord", "-q", "-r", "16000", "-c", "1", "-f", "S16_LE", audio_file]
    else:
        raise RuntimeError("Nenhum utilitário de gravação de áudio encontrado (pw-record, parec, ffmpeg ou arecord).")

def start_recording():
    if not is_voice_enabled():
        return

    if os.path.exists(PID_FILE):
        stop_and_process()
        return

    try:
        record_cmd = get_audio_recorder_cmd(AUDIO_FILE)
    except RuntimeError as e:
        notify("❌ Erro de Áudio", str(e), "dialog-error")
        print(f"[-] {e}")
        return

    proc = subprocess.Popen(record_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    with open(PID_FILE, "w") as f:
        f.write(str(proc.pid))

    notify("🎙️ Gravando áudio...", "Fale sua instrução. Pressione o atalho novamente para colar.", "audio-input-microphone")
    print(f"[+] Gravando ({record_cmd[0]}, PID: {proc.pid})...")

def stop_and_process():
    if not os.path.exists(PID_FILE):
        print("[-] Nenhuma gravação ativa.")
        return ""

    with open(PID_FILE, "r") as f:
        pid = int(f.read().strip())

    try:
        os.remove(PID_FILE)
    except OSError:
        pass

def stop_recording_and_transcribe() -> str:
    """Interrompe gravação, transcreve com Whisper e copia para a área de transferência."""
    if not os.path.exists(PID_FILE):
        return ""

    with open(PID_FILE, "r") as f:
        pid = int(f.read().strip())

    try:
        os.remove(PID_FILE)
    except OSError:
        pass

    # Interrompe o processo de gravação suavemente e aguarda flush do arquivo
    try:
        os.kill(pid, signal.SIGINT)
        for _ in range(15):
            try:
                os.kill(pid, 0)
                time.sleep(0.04)
            except OSError:
                break
    except ProcessLookupError:
        pass

    # Transcrição via whisper-cli
    if not os.path.exists(AUDIO_FILE):
        return ""

    cmd = [
        str(WHISPER_BIN),
        "-m", str(MODEL_PATH),
        "-f", AUDIO_FILE,
        "-l", "pt",
        "-nt",          # sem timestamps
        "-np",          # sem prints internos
        "-t", "6",      # 6 threads para acelerar no Ryzen
        "-bs", "1",     # greedy search (decodificação direta ultrarrápida)
        "-bo", "1",     # 1 candidato
        "-nf",          # sem fallback de temperatura
        "--prompt", TECH_PROMPT,
    ]

    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        text = res.stdout.strip()
    except Exception:
        return ""

    if text:
        with open("/tmp/voice_input_last.txt", "w", encoding="utf-8") as f:
            f.write(text)
        copy_to_clipboard(text)
        print(f"[✓] Transcrição: {text}")

    return text

def stop_and_process() -> str:
    """Modo completo: para, transcreve, copia e cola no terminal."""
    text = stop_recording_and_transcribe()
    if text:
        paste_to_terminal()
    return text

def toggle():
    if os.path.exists(PID_FILE):
        return stop_and_process()
    else:
        start_recording()
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--toggle":
        toggle()
    elif len(sys.argv) > 1 and sys.argv[1] == "--start":
        start_recording()
    elif len(sys.argv) > 1 and sys.argv[1] == "--stop":
        stop_and_process()
    else:
        toggle()
