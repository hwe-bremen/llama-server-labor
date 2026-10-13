# Lab – Kurzanleitung

Ein Befehl startet alles: Router + Chat-UI, Gedächtnis-Proxy (8091), MCP-Server (8787),
Tailscale Serve fürs iPad/iPhone/Mini, `caffeinate` gegen Ruhezustand.
Ausführlich: `RUNBOOK.md`.

## 1. Starten (Fenster 1 – bleibt offen)

**Nur lesen (Normalbetrieb):**
```bash
cd ~/PycharmProjects/llama-server
pkill -f lab_mcp_server; pkill -f lm.proxy; sleep 1
bash scripts/launch_lab_remote.command
```

**Modell darf Dateien schreiben:**
```bash
cd ~/PycharmProjects/llama-server
git status --short                       # sollte leer sein, sonst erst committen
pkill -f lab_mcp_server; pkill -f lm.proxy; sleep 1
bash scripts/launch_lab_remote.command write
```

Fertig, wenn nach 1–3 Min. `Starte Gedaechtnis-Proxy … 8091` erscheint.
Das Gedächtnis ist damit automatisch aktiv – nichts extra einschalten.

**Stoppen:** Ctrl+C in Fenster 1.

## 2. Öffnen

| Wo | Adresse |
|---|---|
| iPad / iPhone / Mini | `https://macbook-pro-von-hans-werner.tail08de73.ts.net` |
| am Mac, mit Gedächtnis | `http://127.0.0.1:8091` |
| am Mac, ohne Gedächtnis | `http://127.0.0.1:8080` |

## 3. Prüfen (Fenster 2, ⌘N)

```bash
curl -s http://127.0.0.1:8091/lm/status | head -c 120; echo
```
Zeile mit `"k": 4` → Gedächtnis aktiv. Leer → Proxy von Hand starten:
```bash
cd ~/PycharmProjects/local-memory
bash lm.command proxy                    # Fenster bleibt offen
```

## 4. Gedächtnis füttern (morgens)

Der Nachtlauf (03:30) bereitet Vorschläge vor. Dann:
```bash
cd ~/PycharmProjects/local-memory
bash lm.command pending                  # ansehen
bash lm.command accept                   # übernehmen  (oder: edit / reject)
```
Von Hand statt Nachtlauf: `bash lm.command memorize`, dann wie oben.
Etwa monatlich aufräumen: `bash lm.command review`, dann `pending`.

## Merksätze

- Jeder Befehlsblock beginnt mit `cd …` – auf den Ordner im Prompt achten.
- Zwei Fenster: 1 = Launcher (nichts eintippen), 2 = Befehle.
- Wechsel lesen ↔ schreiben: in der Web-UI MCP-Eintrag aus/an, Seite neu laden, **neuen Chat**.
- `write` nur bei Bedarf – solange es läuft, darf jeder Chat über `.ts.net` Dateien ändern.
