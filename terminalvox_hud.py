#!/usr/bin/env python3
"""
TerminalVox HUD - Floating Overlay Pill (Wayland / X11)
Mostra feedback visual em tempo real (ondas de áudio, status de transcrição e texto reconhecido).
"""

import os
import sys
import time
import math
import struct
import signal
import threading
import subprocess
from pathlib import Path

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, GLib

import record_and_transcribe as core

HUD_PID_FILE = "/tmp/terminalvox_hud.pid"
NUM_BARS = 16

CSS_STYLES = """
window.hud-window {
    background-color: transparent;
    background: transparent;
}

.hud-pill {
    background-color: rgba(13, 17, 23, 0.94);
    border: 1.5px solid rgba(56, 189, 248, 0.5);
    border-radius: 32px;
    padding: 10px 20px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.7);
}

.hud-title {
    color: #38bdf8;
    font-weight: bold;
    font-size: 13px;
    font-family: monospace, sans-serif;
}

.hud-subtitle {
    color: #e6edf3;
    font-size: 12px;
    font-family: sans-serif;
}

.rec-dot {
    background-color: #ef4444;
    border-radius: 50%;
    min-width: 10px;
    min-height: 10px;
}

.eq-bar {
    background: linear-gradient(180deg, #38bdf8 0%, #a855f7 100%);
    border-radius: 3px;
    min-width: 3px;
}
"""

class TerminalVoxHUD(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.terminalvox.hud")
        self.window = None
        self.eq_bars = []
        self.wave_history = [0.0] * NUM_BARS
        self.smoothed_level = 0.0
        self.anim_source_id = None
        self.is_transcribing = False

    def do_activate(self):
        # 1. Carrega CSS global
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS_STYLES.encode())
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # 2. Cria janela flutuante
        self.window = Gtk.ApplicationWindow(application=self)
        self.window.set_decorated(False)
        self.window.set_resizable(False)
        self.window.set_focusable(False)  # Mantém o foco no terminal ativo
        self.window.add_css_class("hud-window")

        # Container principal (Pílula)
        pill = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        pill.add_css_class("hud-pill")

        # Indicador de gravação (Ponto vermelho)
        self.rec_indicator = Gtk.Box()
        self.rec_indicator.add_css_class("rec-dot")
        self.rec_indicator.set_valign(Gtk.Align.CENTER)

        # Spinner de carregamento (oculto no início)
        self.spinner = Gtk.Spinner()
        self.spinner.set_visible(False)
        self.spinner.set_valign(Gtk.Align.CENTER)

        # Textos de status
        text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        text_box.set_valign(Gtk.Align.CENTER)

        self.title_lbl = Gtk.Label(label="TerminalVox")
        self.title_lbl.add_css_class("hud-title")
        self.title_lbl.set_xalign(0)

        self.status_lbl = Gtk.Label(label="Ouvindo áudio... aperte o atalho para parar")
        self.status_lbl.add_css_class("hud-subtitle")
        self.status_lbl.set_xalign(0)

        text_box.append(self.title_lbl)
        text_box.append(self.status_lbl)

        # Onda de áudio responsiva em tempo real (estilo WhatsApp)
        self.eq_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        self.eq_box.set_valign(Gtk.Align.CENTER)
        self.eq_bars = []
        for _ in range(NUM_BARS):
            bar = Gtk.Box()
            bar.add_css_class("eq-bar")
            bar.set_size_request(3, 4)
            self.eq_box.append(bar)
            self.eq_bars.append(bar)

        # Obtém resolução da tela para ancorar no canto direito superior
        display = Gdk.Display.get_default()
        monitors = display.get_monitors()
        screen_w = monitors.get_item(0).get_geometry().width if monitors.get_n_items() > 0 else 1920
        self.window.set_default_size(screen_w, 90)

        # Container raiz invisível que abrange a largura superior
        root_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        root_box.set_hexpand(True)
        root_box.set_halign(Gtk.Align.FILL)

        # Alinha a pílula no canto superior direito
        pill.set_halign(Gtk.Align.END)
        pill.set_valign(Gtk.Align.START)
        pill.set_margin_end(32)
        pill.set_margin_top(24)

        pill.append(self.rec_indicator)
        pill.append(self.spinner)
        pill.append(text_box)
        pill.append(self.eq_box)

        root_box.append(pill)
        self.window.set_child(root_box)
        self.window.present()

        # Inicia captura de áudio imediatamente
        core.start_recording()

        # Inicia animação da onda de áudio (40ms = 25 FPS)
        self.anim_source_id = GLib.timeout_add(40, self.animate_equalizer)

        # Registra manipulador para o sinal de parada (quando o atalho for apertado de novo)
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGUSR1, self.on_stop_signal)

        # Salva o PID para o atalho saber onde enviar o sinal
        with open(HUD_PID_FILE, "w") as f:
            f.write(str(os.getpid()))

    def get_audio_level(self) -> float:
        """Lê os últimos samples do arquivo WAV gravado e calcula o nível RMS real da voz."""
        audio_file = core.AUDIO_FILE
        chunk_samples = 1024
        try:
            if not os.path.exists(audio_file):
                return 0.0
            size = os.path.getsize(audio_file)
            if size < 44 + (chunk_samples * 2):
                return 0.0
            with open(audio_file, "rb") as f:
                f.seek(-chunk_samples * 2, os.SEEK_END)
                data = f.read(chunk_samples * 2)
            count = len(data) // 2
            if count == 0:
                return 0.0
            samples = struct.unpack(f"<{count}h", data)
            rms = math.sqrt(sum(s * s for s in samples) / count)
            # Escala logarítmica para acompanhar a sensibilidade da fala humana
            # Silêncio fica em ~0.0 e fala normal em ~0.4 a 0.85
            level = max(0.0, min(1.0, (math.log10(max(1.0, rms)) - 1.2) / 2.3))
            return level
        except Exception:
            return 0.0

    def animate_equalizer(self):
        if self.is_transcribing:
            return False

        # Obtém nível real do microfone
        raw_level = self.get_audio_level()

        # Suavização orgânica (ataque rápido, decaimento suave)
        if raw_level > self.smoothed_level:
            self.smoothed_level = self.smoothed_level * 0.3 + raw_level * 0.7
        else:
            self.smoothed_level = self.smoothed_level * 0.75 + raw_level * 0.25

        # Desloca a onda para a esquerda no estilo WhatsApp
        self.wave_history.pop(0)
        self.wave_history.append(self.smoothed_level)

        # Atualiza a altura de cada barra
        for i, bar in enumerate(self.eq_bars):
            # Barra mínima de 4px quando em silêncio, crescendo até 26px conforme a fala
            h = int(4 + self.wave_history[i] * 22)
            bar.set_size_request(3, h)

        return True

    def on_stop_signal(self):
        """Chamado quando o usuário aperta a tecla de atalho novamente."""
        if self.is_transcribing:
            return True

        self.is_transcribing = True

        # Atualiza a interface para o modo "Transcrevendo"
        self.rec_indicator.set_visible(False)
        self.spinner.set_visible(True)
        self.spinner.start()
        self.eq_box.set_visible(False)

        self.title_lbl.set_text("Transcrevendo...")
        self.status_lbl.set_text("Processando com Whisper local...")

        # Roda a transcrição e injeção em uma thread separada para não travar a UI
        threading.Thread(target=self.transcribe_and_finish, daemon=True).start()
        return True

    def transcribe_and_finish(self):
        # 1. Transcreve com Whisper e copia para a área de transferência
        text = core.stop_recording_and_transcribe()

        # 2. Atualiza UI no thread principal do GTK
        GLib.idle_add(self.show_completed_preview, text)

    def show_completed_preview(self, text):
        self.spinner.stop()
        self.spinner.set_visible(False)

        if text:
            self.title_lbl.set_text("✓ Texto Transcrito!")
            preview = (text[:40] + "...") if len(text) > 40 else text
            self.status_lbl.set_text(f"\"{preview}\"")
            # Exibe preview por 450ms, depois fecha a janela e injeta no terminal
            GLib.timeout_add(450, lambda: self.close_and_inject(text))
        else:
            self.title_lbl.set_text("⚠️ Vazio")
            self.status_lbl.set_text("Nenhuma fala detectada.")
            GLib.timeout_add(700, self.cleanup_and_quit)

    def close_and_inject(self, text):
        self.hold()  # Mantém o GTK vivo enquanto o thread cola o texto

        # 1. Fecha a janela para que o GNOME restaure o foco no terminal imediatamente
        if self.window:
            self.window.close()
            self.window = None

        if os.path.exists(HUD_PID_FILE):
            try:
                os.remove(HUD_PID_FILE)
            except OSError:
                pass

        # 2. Em thread, aguarda o foco voltar ao terminal e injeta Ctrl+Shift+V
        def do_paste():
            try:
                time.sleep(0.15)
                core.paste_to_terminal()
            finally:
                self.release()
                GLib.idle_add(self.quit)

        threading.Thread(target=do_paste, daemon=False).start()
        return False

    def cleanup_and_quit(self):
        if os.path.exists(HUD_PID_FILE):
            try:
                os.remove(HUD_PID_FILE)
            except OSError:
                pass
        self.quit()
        return False

def toggle_or_launch():
    """Verifica se o HUD já está aberto. Se estiver, manda parar; se não, abre."""
    # Se o modo de voz estiver desativado pela chave mestre, não faz nada
    if not core.is_voice_enabled():
        return

    if os.path.exists(HUD_PID_FILE):
        try:
            with open(HUD_PID_FILE, "r") as f:
                pid = int(f.read().strip())
            # Envia SIGUSR1 para o processo do HUD transcrever e fechar
            os.kill(pid, signal.SIGUSR1)
            return
        except (ProcessLookupError, ValueError):
            try:
                os.remove(HUD_PID_FILE)
            except OSError:
                pass

    # Abre nova instância do HUD
    app = TerminalVoxHUD()
    app.run([])

if __name__ == "__main__":
    toggle_or_launch()
