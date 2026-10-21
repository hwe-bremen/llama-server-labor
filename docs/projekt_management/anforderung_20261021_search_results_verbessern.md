# Anforderung: search_results_verbessern

Verbindliche Vorgabe von Hawe, woertlich. Spec, Umsetzung und Review werden an diesem Text gemessen;
die Spec ist ein Loesungsvorschlag und kann falsch sein. Nur Hawe aendert diese Datei.

## Aufgabe

> Der wöchentliche Mailversand mit aktuellen Infos zum Entwicklungsstand lokaler LLM soll hinsichtlich der Bereitstellung der Informationen noch verbessert werden:
> 1. llama Infos kommen gut an, jedoch von git-hub werden bisher keine Infos extrahiert, da scheint die Logik noch nicht zu passen. Also funktioniert hier der Abruf bzw. die Wissens/Info Extraction noch nicht wie gewünscht:
> LLAMA_SERVER_URL = os.getenv("LLAMA_SERVER_URL", "http://localhost:8080")
> HF_API_URL = "https://huggingface.co/api/models"
> GITHUB_RELEASES_RSS = [
>     "https://github.com/ggml-org/llama.cpp/releases.atom",
>     "https://github.com/ollama/ollama/releases.atom",
>     "https://github.com/huggingface/transformers/releases.atom"
> 2. Da wir slipstream auch testen, aber erstmal zurückstellen, bis neue interessante Modelle für slipstream in der community diskutiert werden, wäre auch hier ein Infosuche sehr gut. Ergänze also im html eine extra Sektion "Slipstream neueste Entwicklungen" und fasse hier die entsprechenden Resultate zusammen. Bitte erstelle eine Linkliste die entsprechend zu den vorhandenen Zieladressen ergänzt werden kann.
>
> Wenn Du zu dem Auftrag fragen hast melde Dich.

## Antworten auf Rueckfragen

**2026-10-21 10:13** — Frage: **Hast du in den Scout-Logs (`logs/llm_scout_out.log`) schon gesehen, ob die Zeile `RSS https://github.com/...: N Einträge` mit N > 0 kommt?** Wenn ja: Problem liegt im Filter oder in der LLM-Bewertung. Wenn N = 0: Problem liegt im Fetch. Wenn du die Log-Zeile nicht hast oder unsicher bist, sage ich

> HIer ist der Inhalt einer erzeugten MD Datei:
> LLM Scout Weekly
> Top Modelle
> Keine neuen relevanten Modell-Releases gefunden: In der bereitgestellten Liste sind ausschließlich Updates für die llama.cpp Infrastruktur enthalten. Es wurden keine neuen GGUF-Modelle (z. B. von Qwen, Llama, Mistral oder DeepSeek) veröffentlicht, die den Kriterien für Größe (<15GB Q4), Leistung oder Sprache entsprechen.
> Tool Updates
> llama.cpp b11724: Kritischer Bugfix für CUDA-Benutzer. Behebung eines Shared-Memory WAR-Hazards in flash_attn_ext_vec. Dies erhöht die Stabilität und Korrektheit der Inferenz auf NVIDIA-GPUs, ist aber für M4 Macs (Metal Backend) nicht direkt relevant.
> llama.cpp b11723: Verbesserungen für Hexagon-Backends (Qualcomm Snapdragon). Fokus auf längere Kontexte und Sliding Window Attention (SWA). Relevant nur für Nutzer von Android/Qualcomm-Hardware, nicht für Apple Silicon.
> llama.cpp b11722: Ermöglicht Multistream Flash Attention für Hexagon. Ebenfalls spezifisch für Qualcomm-Hardware-Optimierungen.
> Fazit
> Ein Update lohnt sich aktuell nur, wenn du NVIDIA-GPUs nutzt (wegen des CUDA-Fixes in b11724); für M4 Macs sind diese Releases irrelevant, da sie sich auf CUDA und Hexagon konzentrieren.
>
> _____
>
> Nur Llama inhakte kein github, kein hugging face
>
> ____
>
> ZU slipsream:  hier das repro https://github.com/chenzhuofu/slipstream oder z.B.: https://huggingface.co/blog/anthonym21/slipstream-for-agent-communication

**2026-10-21 10:31** — Frage: **Welchen Umfang willst du für die Spec?** Nur A, oder A+B?

> A und B, und zwar B zuerst: erst ein Lauf, der pro Quelle protokolliert, was abgerufen, gefiltert und an das Modell gegeben wurde, dann der Fix.
> Zusätzlich verbindlich:
>
> Im Bericht muss für jede Quelle sichtbar sein, was gefunden wurde, auch „nichts Neues“: Hugging Face, jedes GitHub-Repo einzeln, Slipstream. Keine Quelle darf eine andere verdrängen.
> Korrektur Slipstream: Meine beiden Links waren falsch. Gemeint ist ausschließlich das Projekt https://github.com/Schero94/slipstream (Releases) sowie Diskussionen zu MoE-Expert-Streaming von der SSD. Der Name „Slipstream“ ist mehrdeutig, es gibt viele fremde Projekte gleichen Namens. Die dürfen nicht im Bericht landen.
> Die Linkliste soll ohne Codeänderung erweiterbar sein.
>
> Dann Spec schreiben.

**2026-10-21 11:15**

> Nachtrag:
> OQ1: nur agents/llm_scout/sources.json im Repo, kein Fallback; fehlt sie, Exit 1.
> OQ2: Atom-Feed https://github.com/Schero94/slipstream/releases.atom.
> OQ3/OQ4: HF-Blog streichen. Slipstream ist ausschließlich das Repo Schero94/slipstream (Releases). Weitere Quellen später nur über sources.json.
> OQ5: JSON.
> OQ6: source_run_log_<KW>.jsonl, eine Zeile pro Lauf, anhängen.
> OQ7: keine Grenze, Warnung ab 8 Repos.
> Bitte Spec entsprechend anpassen (A3, Quellen, Tests T4/T10) und die offenen Fragen als entschieden markieren.

