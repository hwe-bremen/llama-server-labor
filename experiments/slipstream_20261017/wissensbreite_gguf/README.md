# Wissensbreite GGUF — Qwen3-Coder-Next 80B gegen Qwen3.6 (und Qwen3.8)

Frage: Hat Qwen3-Next mehr **Wissensbreite** als Qwen3.6? Nur wenn ja, lohnen Modellwahl in der Kette und Nachtlauf
(siehe Slipstream-Stand im Claude-Projekt). Aufgabe: GGUF-Leser in reinem Python (Teil A, maschinell bewertet) und
7 Wissensfragen (Teil B, von Hand gegen den Schlüssel). Der **Schlüssel liegt nur im Claude-Projekt**
(`claude/wissensbreite-gguf-schluessel.md`), nicht hier. **Ergebnis 20.10.: `AUSWERTUNG.md`.**

- Einzelanfrage per API, ohne Tools, ohne Thinking, Temperatur 0,2, 3 Läufe je Modell.
- Referenz ist `gguf-py` aus `../qwen3next_reproducible_build/upstream/gguf-py` (gleicher llama.cpp-Stand wie die Builds).
- Prüfdateien: D1 `synth_klassisch.gguf` (erzeugt, alle Werttypen, Alignment 64, 27 Tensortypen), D2–D4 echte Modelle.
- Modellcode wird nur von `pruefen.py` ausgeführt: vorher AST-Prüfung (Nicht-Standard-Import → disqualifiziert;
  `subprocess`/`socket`/`os.system`/Schreibzugriffe u. ä. → nicht ausgeführt), dann `python3 -I` im leeren Temp-Ordner, 120 s.

## Kurzweg: Starter (findet die Dateien selbst, kein Kopieren nötig)

```bash
bash experiments/slipstream_20261017/wissensbreite_gguf/start_wissensbreite.command router    # Lab per start_eval.command
bash experiments/slipstream_20261017/wissensbreite_gguf/start_wissensbreite.command next      # nach purge + launch_qwen3next
bash experiments/slipstream_20261017/wissensbreite_gguf/start_wissensbreite.command bewerten
```

`router` = Selbsttest, Referenz, dann je 3 Läufe Qwen3.6, Qwen3.8, Mellum2-12B Q4_K_M. Modelle mit schon 3 fertigen
Läufen werden übersprungen. Logs und `TABELLE.md` landen in `ergebnisse/`.

## Ablauf von Hand (aus dem Repo-Root)

```bash
W=experiments/slipstream_20261017/wissensbreite_gguf
.venv/bin/pip install numpy pyyaml                       # falls noch nicht da (gguf-py braucht beides)
.venv/bin/python -m unittest -v $W/selbsttest/test_pruefen.py   # 15 Gegenproben, erzeugt D1 + Bonusdatei
.venv/bin/python $W/pruefen.py referenz <D2.gguf> <D3.gguf> <D4.gguf>   # Pfade prüfen, Referenz vorrechnen

# Router-Modelle (start_eval.command, 1 Modell im Speicher)
python3 $W/lauf.py --url http://127.0.0.1:8080 --modell "unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL"
python3 $W/lauf.py --url http://127.0.0.1:8080 --modell "unsloth/Qwen3.8-27B-GGUF:Q4_K_XL"
# Lab beenden, sudo purge, dann scripts/launch_qwen3next.command (Port 8083)
python3 $W/lauf.py --url http://127.0.0.1:8083 --modell Qwen3-Coder-Next-80B-A3B

.venv/bin/python $W/pruefen.py bewerten --bonus $W/ergebnisse/*/ --dateien <D2> <D3> <D4>
.venv/bin/python $W/pruefen.py tabelle $W/ergebnisse
```

Je Lauf entstehen `antwort_a.md`, `gguf_lesen.py`, `wissen.json`, `meta.json`, nach dem Bewerten `bewertung.md/.json`.
Teil B bewertet Claude gegen den Schlüssel.

## Dateien
- `aufgabe.md` – Prompt Teil A (wortgleich an alle Modelle)
- `fragen.json` – Teil B, nur Fragen
- `lauf.py` – Anfragen (nur Standardbibliothek)
- `pruefen.py` – synthetische Dateien, Referenz aus gguf-py, Ausführen + Vergleich, Tabelle
- `start_wissensbreite.command` – Starter (router / next / bewerten)
- `selbsttest/` – Musterlösung (Claude) und Gegenproben des Prüfers
- `ergebnisse/` – Läufe 20.10. (Modellantworten, Code, Bewertungen, Logs)
- `AUSWERTUNG.md` – Ergebnis
