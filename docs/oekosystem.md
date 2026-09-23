# Ökosystem-Raster — wo gehört welches Tool hin?

Orientierungshilfe, um neue Tools (LM Studio, Ollama, MLX, Bionic, vLLM ...)
schnell einzuordnen, statt sie einzeln zu lernen. Stand: 22.09.2026.

## Die fünf Schichten

Fast alles im Local-LLM-Ökosystem ist genau eine dieser Schichten — oder ein
Bündel aus mehreren.

| # | Schicht | Aufgabe | Beispiele |
|---|---------|---------|-----------|
| 1 | **Modell** | die Gewichte | Apertus, Qwen3.6, Mellum2, Gemma 4 |
| 2 | **Engine** | rechnet | llama.cpp, MLX, vLLM |
| 3 | **Server** | stellt eine API bereit | llama-server, `mlx_lm.server`, LM Studio, Ollama |
| 4 | **Oberfläche** | Chat per Klick | llama-server Web-UI, LM Studio Chat, Open WebUI |
| 5 | **Agent** | handelt selbstständig | Cline, LM Studio Bionic, `core/mcp_agent.py` |

Die **OpenAI-kompatible API** auf Schicht 3 ist die Steckdose, die alles
verbindet. Fast jeder Server spricht sie, deshalb laufen die eigenen Clients
unverändert weiter, wenn man Engine oder Server tauscht. Es ändert sich nur
der Port.

## Schicht 1: Dateiformate

Ein Modell ist nur nutzbar, wenn **beides** stimmt: Format passt zur Engine,
UND die Engine kennt die Architektur.

| Format | Engine | Anmerkung |
|--------|--------|-----------|
| safetensors | vLLM, Transformers | das Original, meist für Nvidia-GPUs |
| GGUF | llama.cpp | unser Standard |
| MLX | MLX (Apple) | Apple-Silicon-eigenes Framework |

**Beispiel Apertus:** Version 1.0 (2509) läuft als GGUF in llama-server.
Version 1.5 hat eine neue, multimodale Architektur (`apertus1p5`), die
llama.cpp nicht kennt — es gibt also kein GGUF. Wer 1.5 lokal will, braucht
MLX plus einen Community-Umbau auf reinen Text, oder vLLM.

## Was Produkte bündeln

Verwirrung entsteht fast immer dadurch, dass ein Produkt mehrere Schichten
zusammenfasst:

- **llama-server** = Server + Oberfläche (Engine: llama.cpp)
- **Ollama** = Engine + Server
- **LM Studio** = Engine + Server + Oberfläche
- **LM Studio Bionic** = Agent, eigene App, setzt auf der LM-Studio-Runtime auf
- **MLX** = nur Engine; die API kommt separat über `mlx_lm.server`

## Dieses Lab im Raster

```
Mellum2 / Qwen3.6 / Gemma 4 / Apertus 1.0   (GGUF)
              ↓
          llama.cpp                          (Engine)
              ↓
   llama-server Router, Port 8080            (Server + Web-UI)
              ↓
   Web-UI  |  core/mcp_agent.py  |  Cline    (Oberfläche / Agent)
```

MLX wäre eine **zweite Engine mit eigenem Server** an derselben Steckdose,
kein Ersatz. Beide können parallel laufen, auf verschiedenen Ports.

## Leitfrage bei jedem neuen Tool

> Welche Schicht(en) ist das, und welches Modellformat braucht es?

Damit ist die Apertus-1.5-Frage in zwei Minuten geklärt: kein GGUF, also
kein llama-server — unabhängig davon, wie gut das Modell ist.

## Zwei Stolperfallen aus der Praxis

1. **Gleiches Modell, anderes Template.** Ein GGUF enthält auch das
   Chat-Template. Bei Apertus 8B brachte die Variante von MaziyarPanahi den
   kompletten Server beim Template-Parsing zum Absturz, die von jondale
   (gleiche Gewichte, korrigiertes Template) läuft sauber. Bei Problemen also
   zuerst das Template verdächtigen, nicht die Engine.
2. **Einzelmodell vs. Router.** `llama-server -hf <repo>` lädt genau ein
   Modell — dann steht auch nur dieses im Dropdown. Die volle Liste gibt es
   nur im Router-Modus über `--models-preset config/models.ini`
   (`scripts/launch_router.command`).
