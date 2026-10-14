#!/usr/bin/env python3
"""
Botão Flutuante de Voz (Widget GTK4) para Ubuntu
Permite gravar pelo clique de um botão e colar no terminal do agente de IA.
"""

import sys
import threading
from pathlib import Path

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib

import record_and_transcribe as core

class VoiceButtonApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.agente.voiceinput")
        self.is_recording = False

    def do_activate(self):
        self.win = Gtk.ApplicationWindow(application=self, title="Voice Input")
        self.win.set_default_size(260, 90)
        self.win.set_resizable(False)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(16)
        box.set_margin_end(16)

        self.btn = Gtk.Button(label="🎙️ Gravar Voz")
        self.btn.connect("clicked", self.on_button_clicked)
        self.btn.set_css_classes(["suggested-action"])

        self.status = Gtk.Label(label="Pronto para ditar")
        self.status.set_wrap(True)

        box.append(self.btn)
        box.append(self.status)

        self.win.set_child(box)
        self.win.present()

    def on_button_clicked(self, button):
        if not self.is_recording:
            self.is_recording = True
            self.btn.set_label("⏹️ Parar e Transcrever")
            self.btn.set_css_classes(["destructive-action"])
            self.status.set_text("Gravando... Fale agora")
            core.start_recording()
        else:
            self.is_recording = False
            self.btn.set_label("⏳ Processando...")
            self.btn.set_sensitive(False)
            self.status.set_text("Transcrevendo áudio localmente...")

            def worker():
                text = core.stop_and_process()
                GLib.idle_add(self.on_transcription_finished, text)

            threading.Thread(target=worker, daemon=True).start()

    def on_transcription_finished(self, text):
        self.btn.set_label("🎙️ Gravar Voz")
        self.btn.set_css_classes(["suggested-action"])
        self.btn.set_sensitive(True)
        if text:
            display_text = (text[:35] + '...') if len(text) > 35 else text
            self.status.set_text(f"✓ \"{display_text}\"")
        else:
            self.status.set_text("Pronto para ditar")

if __name__ == "__main__":
    app = VoiceButtonApp()
    app.run(sys.argv)
