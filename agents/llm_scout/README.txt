# Local LLM Scout

Wöchentlicher Agent, der nach neuen lokalen LLM-Modellen und Tool-Updates sucht.

## Features
- Sucht nach neuen GGUF-Modellen auf Hugging Face.
- Prüft GitHub Releases für llama.cpp, Ollama, Transformers.
- Nutzt ein lokales LLM (via llama-server) zur Bewertung der Relevanz.
- Erstellt ein Markdown-Infopaper in `~/lab/weekly-reports/`.

## Einrichtung

1. **Abhängigkeiten installieren:**
   ```bash
   pip install -r requirements.txt