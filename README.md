# Baguette

<p align="center">
  <img src="assets/preview.png" alt="Preview" width="100%">
</p>

<p align="center">
  <strong>A terminal-native AI agent built for developers.</strong>
</p>

Baguette is a modern, terminal-native AI agent built for developers who live in the command line. Inspired by operating system kernels, it replaces traditional chat interfaces with a clean, keyboard-first experience focused on speed, structure, and productivity.

Designed to be model-agnostic, Baguette lets you seamlessly switch between local and cloud AI providers while maintaining a consistent user experience.

---

## Features

- Terminal-first, keyboard-driven interface
- Clean kernel-inspired UI
- Multiple AI providers
  - Ollama
  - Anthropic
  - OpenAI
  - Google Gemini
  - Groq
- Switchable personas (`/persona`)
- Runtime model switching (`/model`)
- Extensible architecture for future tools and providers
- Lightweight and fast

---

## Installation

### Prerequisites

- Python 3.10+
- Git

### Clone the repository

```bash
git clone https://github.com/yourusername/Baguette.git
cd Baguette
```

### Create a virtual environment

**Windows**

```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install dependencies

```bash
pip install -e .
```

---

## Usage

Launch Baguette:

```bash
Baguette
```

### Built-in Commands

```text
/model      Change the active AI model
/provider   Switch AI provider
/persona    Change the assistant personality
/help       Show available commands
/clear      Clear the terminal
/exit       Exit Baguette
```

---

## Philosophy

Baguette is built around a simple philosophy:

- Terminal-native
- Keyboard-first
- Model-agnostic
- Fast
- Minimal
- Extensible

The goal is to make AI feel like a natural extension of the terminal rather than another chat application.

---

## License

Licensed under the MIT License.
