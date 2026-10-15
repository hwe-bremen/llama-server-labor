# Review-Eval — welches Modell prüft am besten?

Kleiner, eigener Prüfstein statt fremder Benchmark-Tabellen: Jedes Kandidaten-Modell prüft
**dieselbe eingefrorene Aufgabe** mit **demselben Review-Prompt**. Gezählt wird, wie viele
bekannte Befunde es findet, was es erfindet und ob es den Code wirklich per Tool liest.

Der Lösungsschlüssel liegt **nicht im Repo** (die Review-Instanz kann das ganze Repo lesen),
sondern im claude.ai-Projekt (`claude/review-eval-schluessel.md`).

## Aufgabe `scout_20261014`

Ordner `scout_20261014/`: Handover der llm_scout-Automatisierung samt Code, plist und Logs im
Stand vom 14.10.2026 — vor den späteren Fixes. Nicht anfassen, nicht reparieren: Das ist
Testmaterial.

## Start (einmal für alle Läufe)

```bash
LAB_MODELS_MAX=1 ROLE_UPSTREAM=http://127.0.0.1:8080 bash scripts/launch_lab_roles.command
```

- `LAB_MODELS_MAX=1`: immer nur ein Modell im Speicher; der Router lädt beim Wechsel um.
- `ROLE_UPSTREAM=…8080`: Rollen-Proxy **direkt auf den Router**, am Gedächtnis-Proxy vorbei.
  Grund: Über 8091 wird Qwen ohne Thinking gefahren (`LM_NO_THINK`) und das Gedächtnis mischt
  Text in den Prompt — beides würde den Modellvergleich verfälschen. So läuft jedes Modell mit
  seinem Preset aus `config/models.ini`.
- Browser `http://127.0.0.1:8092` (MCP-Eintrag dort vorhanden).

## Ablauf je Kandidat

1. **Neuer Chat**, Modell im Dropdown wählen. Erster Aufruf eines neuen Modells lädt es von
   Hugging Face (~18 GB) — das dauert, im Launcher-Fenster sichtbar.
2. Genau dieser Text, unverändert:

```
@review Prüf das Handover role-split/eval/scout_20261014/handover_20261014_llm_scout_automation.md gegen den Code und die Logs in diesem Ordner (llm_scout.py, llm_scout.plist, logs/). Prüfe ausschließlich die Dateien in role-split/eval/scout_20261014/, nicht die gleichnamigen Dateien anderswo im Repo. Es gibt keine Spec; die Anforderungen stehen im Handover. Speichere das Verdikt als verdict_20261014_eval_scout_<modellkürzel>.md.
```

3. Nicht nachhelfen. Fragt das Modell nach, kurz antworten, ohne Hinweise auf Befunde.
   Bleibt es hängen oder speichert nicht: einmal „Speichere das Verdikt jetzt." — und notieren.
4. Notieren: Start- und Endzeit, Tool-Aufrufe sichtbar ja/nein, Nachfragen/Nachhilfen.

Das Modellkürzel setzt der Rollen-Proxy in den Prompt (Familie + Version + Größe), die Dateien
überschreiben sich deshalb nicht.

## Kandidaten (alle Q4_K_XL, damit Modelle verglichen werden, nicht Quantisierungen)

| Modell | Familie | Kürzel → Verdikt-Datei | Größe |
|---|---|---|---|
| unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL | Qwen | `qwen36-27b` | vorhanden |
| unsloth/Qwen3.8-27B-GGUF:Q4_K_XL | Qwen | `qwen38-27b` | 17,6 GB, wird geladen |
| unsloth/gemma-4-26B-A4B-it-GGUF:Q4_K_XL | Gemma | `gemma4-26b` | vorhanden |
| unsloth/gemma-4-31B-it-GGUF:Q4_K_XL | Gemma | `gemma4-31b` | 18,8 GB, wird geladen |

Reihenfolge-Vorschlag: zuerst die beiden vorhandenen (kein Download), dann die neuen.

## Auswertung

Claude oder Hawe legt jedes Verdikt neben den Lösungsschlüssel:

| Messpunkt | Wie |
|---|---|
| Treffer | Pflichtbefunde gefunden (je 1, halb 0,5) |
| Erfindungen | Befunde ohne passende Fundstelle, falsche Pfade/Optionen, erfundene Tests |
| Urteil | PASS / NACHBESSERN / FAIL — passt es zu den Befunden? |
| Werkzeugtreue | Code wirklich per Tool gelesen („Geprüfte Dateien", Tool-Aufrufe in der UI)? |
| Form | Vorlage eingehalten, Datei gespeichert, Modellname korrekt |
| Zeit | Minuten bis zum Verdikt |

Ergebnis: das High-End-Paar für den Doppel-Review — das stärkste Modell plus das stärkste aus
einer **anderen** Familie.

Vorbehalt: Eine Aufgabe ist eine Stichprobe. Bei knappen Ergebnissen eine zweite Aufgabe
einfrieren (z. B. das nächste echte Handover) und wiederholen.
