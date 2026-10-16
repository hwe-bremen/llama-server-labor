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
bash start_eval.command      # ab 16.10.; gleichwertig: LAB_MODELS_MAX=1 MCP_ALLOW_GITLOG=0 ROLE_UPSTREAM=http://127.0.0.1:8080 LAB_BIND=serve bash scripts/launch_lab_roles.command
```

- `LAB_MODELS_MAX=1`: immer nur ein Modell im Speicher; der Router lädt beim Wechsel um.
- `ROLE_UPSTREAM=…8080`: Rollen-Proxy **direkt auf den Router**, am Gedächtnis-Proxy vorbei.
  Grund: Über 8091 wird Qwen ohne Thinking gefahren (`LM_NO_THINK`) und das Gedächtnis mischt
  Text in den Prompt — beides würde den Modellvergleich verfälschen. So läuft jedes Modell mit
  seinem Preset aus `config/models.ini`.
- Browser `http://127.0.0.1:8092` (MCP-Eintrag dort vorhanden).
- `MCP_ALLOW_GITLOG=0` (ab 16.10.): `git_log` aus. Die Fix-Commits der Aufgabe stehen in der
  Git-Historie und verraten sonst die Lösung (Qwen3.8 hat `5065ba4` zitiert). Läuft auf 8787
  schon ein MCP-Server ohne diesen Schalter, bricht der Starter ab (fail-loud).
- Web-UI ab llama.cpp 0.6.0: unter Settings → Tools die eingebauten Tools („Browser":
  get_datetime, get_info) **aus**, damit alle Kandidaten dieselben Tools haben.
- Neue Modelle **vorher** herunterladen, nicht im Eval-Chat:
  `curl -s -X POST http://127.0.0.1:8080/models/load -H 'Content-Type: application/json' -d '{"model":"<id>"}'`,
  warten bis `curl -s http://127.0.0.1:8080/models` für das Modell `loaded` meldet. Sonst bricht
  der Browser die Anfrage während des Downloads ab (Befund 15.10.).

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
| unsloth/Qwen3.8-27B-GGUF:Q4_K_XL | Qwen | `qwen38-27b` | 17,6 GB, vorhanden |
| unsloth/gemma-4-26B-A4B-it-GGUF:Q4_K_XL | Gemma | `gemma4-26b` | vorhanden |
| unsloth/gemma-4-31B-it-GGUF:Q4_K_XL | Gemma | `gemma4-31b` | 18,8 GB, vorhanden |

Reihenfolge-Vorschlag: zuerst die beiden vorhandenen (kein Download), dann die neuen.

## Prompt- und Werkzeugstand

| Stand | Was | Läufe |
|---|---|---|
| v1 | `review.md` bis 15.10.; `search_files` mit Dateipfad still leer; `git_log` an | Qwen3.6, Gemma 26B, Gemma 31B, Qwen3.8 (14.–16.10.) |
| v2 | `review.md` mit Schritt „Fehlerpfade durchspielen" und Urteilsregel (PASS nur ohne hohen Befund); `search_files` repariert; `git_log` aus | ab 16.10. |

v1 und v2 nicht direkt vergleichen: v2 misst, ob Prompt und Werkzeuge helfen.
Vorbehalt: Der Fehlerpfad-Schritt wurde nach den Lücken **dieser** Aufgabe formuliert. Ob er
allgemein hilft oder nur hier, zeigt erst eine zweite, neue Aufgabe.

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

## Halluzinations-Probe (Vortest, vor jedem neuen Modell)

Bevor ein neues Modell ins Review-Eval geht: `python3 role-split/eval/halluzination/probe.py --modelle "<id>"`.
11 feste Fragen per API ohne Tools (erfundene Begriffe, Texttreue, Fakten), je ohne und mit Rolle
`research`. Ergebnis in `halluzination/ergebnisse/`. Details: `halluzination/README.md`.
