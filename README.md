<p align="center">
  <img src="assets/banner.jpg" alt="TerminalVox Logo" width="680" style="border-radius: 12px;" />
</p>

<h1 align="center">TerminalVox 🎙️</h1>

<p align="center">
  <b>Ditado de voz instantâneo e 100% offline para terminais Linux e agentes de IA.</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Licen%C3%A7a-MIT-blue.svg" alt="Licença: MIT">
  <img src="https://img.shields.io/badge/Plataforma-Linux%20(Wayland%20%2F%20X11)-orange.svg" alt="Plataforma: Linux">
  <img src="https://img.shields.io/badge/%C3%81udio-PipeWire%20%7C%20PulseAudio%20%7C%20ALSA-green.svg" alt="Motores de Áudio">
  <img src="https://img.shields.io/badge/Motor-Whisper.cpp%20(Local)-purple.svg" alt="Motor Whisper.cpp">
</p>

---

O **TerminalVox** é uma ponte de voz-para-texto (*speech-to-text*) ultrarrápida, nativa e 100% offline, projetada especialmente para desenvolvedores Linux que interagem com **agentes de IA no terminal** (como Antigravity, Claude Code, Aider, Cursor CLI) e ambientes de linha de comando em geral.

Pressione o atalho, dite sua instrução técnica ou comando shell, pressione novamente, e o texto transcrito é colado automaticamente direto no cursor do seu terminal ativo.

---

## ✨ Recursos

* 🔒 **100% Local e Privado:** Sem APIs externas, sem custos, sem nuvem e sem envio de dados pela rede. Seus áudios nunca saem da sua máquina.
* ⚡ **Resposta Ultrarrápida (~1.5s):** Utiliza `whisper.cpp` compilado e otimizado para o seu processador (AVX2 + multithreading + decodificação direta gulosa).
* 🌊 **HUD Flutuante com Ondas de Áudio:** Janela flutuante minimalista em GTK4 no canto superior direito, com barras responsivas em tempo real que reagem à amplitude da sua voz (estilo WhatsApp).
* 🧠 **Vocabulário Técnico de Programação:** Calibrado com prompts contextuais de desenvolvimento (*branch, merge, commit, master, build, pull request, ESP32, Python, Linux, Docker, etc.*).
* ⌨️ **Injeção Direta no Terminal:** Cola automaticamente o texto no terminal em foco (via `ydotool` no Wayland ou `xdotool` no X11), pronto para envio.
* 🛡️ **Chave Geral de Segurança (Master Switch):** Atalho global para ligar/desligar o modo de voz, garantindo que o microfone só fique acessível quando você desejar.
* 🐧 **Compatibilidade Universal no Linux:** Funciona em **Ubuntu, Debian, Fedora, Arch Linux, Pop!_OS, openSUSE**, tanto sob **Wayland** quanto **X11**.

---

## 🚀 Instalação Rápida e Automatizada

Basta clonar o repositório e executar o script de instalação universal:

```bash
git clone https://github.com/SEU_USUARIO/TerminalVox.git
cd TerminalVox
./install.sh
```

O script cuida de todo o processo de forma automática:
1. **Detecta sua distribuição Linux** e instala as dependências do sistema (`apt`, `dnf`, `pacman` ou `zypper`).
2. **Configura o teclado virtual (`/dev/uinput`)** para permitir a digitação automática em sessões Wayland.
3. **Clona e compila o `whisper.cpp`** com otimizações nativas de CPU.
4. **Baixa o modelo base multilíngue** do Whisper.
5. **Configura as permissões** e deixa o sistema ativado por padrão.

---

## 🎯 Como Usar (Sistema de Atalhos Duplo)

O TerminalVox opera através de um fluxo seguro e prático de **dois atalhos globais**:

### Passo 1: Chave Geral (Ligar / Desligar)
* **Atalho sugerido:** `Super + Alt + V` (ou `F7`, `Shift + BackSpace`)
* **Comando:** `/caminho/para/TerminalVox/voice_master_switch.sh`
* **O que faz:**
  * Exibe notificação de sistema: **🎙️ TerminalVox ATIVADO**.
  * Desbloqueia o atalho de gravação para uso.
  * *(Ao pressionar novamente, desliga o sistema: **🔇 TerminalVox DESATIVADO**, desativando o microfone para evitar acionamentos acidentais).*

### Passo 2: Gravar e Injetar no Terminal
* **Atalho sugerido:** `F8` (ou `Pause`, `Shift + Espaço`)
* **Comando:** `/caminho/para/TerminalVox/voice_toggle.sh`
* **Como utilizar:**
  1. **Pressione o atalho uma vez:** O HUD flutuante surge no canto superior direito exibindo as ondas sonoras que reagem dinamicamente à sua voz.
  2. **Fale naturalmente:** Dite seus comandos git, instruções de código ou perguntas para o seu agente de IA.
  3. **Pressione o atalho novamente:**
     * O HUD muda para um spinner animado enquanto transcreve o áudio localmente via Whisper.
     * Mostra uma breve confirmação visual (`✓ Texto Transcrito!`).
     * O HUD fecha suavemente e **cola o texto diretamente no prompt do seu terminal**.
  4. **Pressione `Enter`** para executar ou enviar o prompt ao agente!

---

## 🖥️ Configuração dos Atalhos no Sistema

### GNOME (Ubuntu, Fedora, Pop!_OS)
1. Abra **Configurações** > **Teclado** > **Atalhos do Teclado** > **Atalhos Personalizados** (`+`).
2. Cadastre os dois atalhos:
   * **Chave Geral:** `/caminho/para/TerminalVox/voice_master_switch.sh`
   * **Gravar / Injetar:** `/caminho/para/TerminalVox/voice_toggle.sh`

### KDE Plasma
1. Abra **Configurações do Sistema** > **Atalhos** > **Atalhos Personalizados**.
2. Adicione **Atalho Global** > **Comando/URL** apontando para os respectivos scripts.

### Tiling Window Managers (Hyprland, Sway, i3)
Adicione ao seu arquivo de configuração (ex.: `hyprland.conf`):
```conf
bind = $mainMod ALT, V, exec, /caminho/para/TerminalVox/voice_master_switch.sh
bind = , F8, exec, /caminho/para/TerminalVox/voice_toggle.sh
```

---

## 📄 Licença

Este projeto está sob a licença [MIT](LICENSE).
