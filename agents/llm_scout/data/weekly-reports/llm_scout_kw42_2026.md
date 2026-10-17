# LLM Scout Weekly

## Top Modelle
- **Keine neuen Modell-Releases in dieser Liste**: Die bereitgestellten Daten enthalten ausschließlich Updates für die Infrastruktur-Software `llama.cpp`. Es wurden keine neuen GGUF-Modelle (wie z.B. von Qwen, Llama, Mistral oder DeepSeek) freigegeben.

## Tool Updates
- **[llama.cpp v0.7.0](https://github.com/ggml-org/llama.cpp/releases/tag/v0.7.0)**: Dies ist ein signifikantes Major-Update.
    - **LiliCorr Speculative Decoding**: Eine neue Technik zur Beschleunigung der Inferenz, die besonders bei Modellen mit ähnlicher Architektur zum "Draft-Modell" effizient sein kann.
    - **MTP für GLM-4/5-Next**: Unterstützung für Multi-Token Prediction, was die Geschwindigkeit bei bestimmten Modellen (wie ZhipuAI's GLM-Reihe) erhöhen kann.
    - **Neuer GPU Cache für MoE**: Die Option `--moe-cache-mib` erlaubt es, Experten von Mixture-of-Experts-Modellen im Host-Speicher (RAM) zu cachen, was die Latenz bei Modellen wie Mixtral oder Qwen-MoE auf Systemen mit begrenztem VRAM (aber viel RAM, wie deinem M4 Mac) verbessern kann.

## Fazit
Ein Update auf `llama.cpp v0.7.0` lohnt sich definitiv, insbesondere wenn du MoE-Modelle (wie Mixtral 8x7B oder Qwen2.5-MoE) oder GLM-Modelle lokal ausführen möchtest, da die neuen Caching- und Decoding-Techniken die Performance auf deinem M4 Mac mit 48GB RAM spürbar optimieren können.