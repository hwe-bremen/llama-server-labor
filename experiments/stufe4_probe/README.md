# Stufe-4-Sonde: lange Werkzeugaufrufe in der Web-UI (8092)

Ziel: vor der Stufe-4-Spec **messen**, nicht raten – wo sitzt das Zeitlimit für
MCP-Werkzeugaufrufe, und wie stellt die UI „Lauf gestartet → Status abfragen" dar.

Kette eines Werkzeugaufrufs mit „use llama-server proxy":
`Browser → 8092 role_proxy → 8091 local-memory → 8080 --ui-mcp-proxy → 8789 Sonde`

Bekannte bzw. vermutete Zeitlimits (kürzestes gewinnt):

| Glied | Limit | Status |
|---|---|---|
| role_proxy.py | Socket-Timeout 900 s | im Code gelesen |
| local-memory 8091 | ? | nicht geprüft (anderes Repo) |
| llama-server `--timeout` | Vermutung: 600 s Default | mit `llama-server --help \| grep -i timeout` prüfen |
| MCP-Client der Web-UI | ? | genau das misst die Sonde |
| Tailscale Serve (iPad) | ? | nur Schritt 5 |

## Start

```bash
bash start_rollen.command                          # Fenster 1, wie immer
bash experiments/stufe4_probe/start_probe.command  # Fenster 2
```

Web-UI `http://127.0.0.1:8092` → MCP-Server hinzufügen: `http://127.0.0.1:8789/mcp`,
per Stift „use llama-server proxy" **AN**, Seite neu laden, **neuer Chat**.
Den Lab-Eintrag (8787) für die Messung ausschalten, damit das Modell nur die Sonde sieht.

## Messreihe (je ein neuer Chat, Uhrzeit notieren)

1. `Rufe probe_warten mit sekunden=30 auf.` → Gegenprobe, sollte glatt gehen
2. `probe_warten` mit **120**, dann **330**, dann **620** – bis die UI einen Fehler zeigt
3. Bei der ersten Fehlerstufe: dasselbe mit `probe_warten_fortschritt`
   (verlängert Fortschritt das Limit? zeigt die UI ihn an?)
4. `Starte probe_start mit sekunden=300.` → dann im selben Chat mehrfach
   `Wie ist der Stand?` – ruft das Modell `probe_status` mit der richtigen ID selbst?
   Zweiter `probe_start` während des Laufs → kommt „Abgelehnt" sauber an?
5. Optional iPad über `.ts.net`: Schritt 2 mit der Stufe knapp unter dem Mac-Limit

## Auswertung

```bash
tail -n 40 ~/.lab_mcp/probe_calls.jsonl
```

Lesart: `abgebrochen` im Log = der Client hat aktiv `notifications/cancelled` geschickt
(so macht es die Web-UI). `ok` nach dem UI-Fehler hieße: ein Glied hat nur aufgehört zu
warten, ohne abzubrechen (so verhält sich ein einfacher Python-Client).

## Ergebnis 28.10.2026 (Mac, 8092, Qwen3.6-27B-MTP Q4_K_XL)

| Schritt | Ergebnis |
|---|---|
| 1 `probe_warten` 30 s | ok |
| 2 `probe_warten` 120 s | ok (120,1 s) |
| 2 `probe_warten` 330 s | UI: `MCP error -32001: Request timed out`; Sonde: `abgebrochen nach 322,7 s` nach `POST 202` (Cancel der UI) |
| 3 `probe_warten_fortschritt` 330 s | gleicher Fehler – Fortschritt verlängert das Limit **nicht** |
| 4 `probe_start` 300 s + `probe_status` | ok: ID gemerkt, Status selbst abgefragt, Sperre korrekt erklärt, „fertig nach 300,0 s" |

Folgerungen für die Stufe-4-Spec:
- Das Limit sitzt im **MCP-Client der Web-UI** (~5 min; Vermutung: 300-s-Zähler, der vor dem
  eigentlichen Aufruf startet). Proxys (900 s) und llama-server greifen vorher nicht.
- Die UI **bricht aktiv ab** – ein blockierendes Werkzeug wird mittendrin abgewürgt.
  → `kette_lauf` startet einen **eigenen Prozess** (nicht Thread im Werkzeugaufruf),
  kehrt sofort zurück, Sperrdatei gegen Doppelstart. Faustregel: kein Werkzeug > ~4 min blockierend.
- Bedienmuster Start → Status trägt mit dem 27B; das Modell deutet Fehler aber selbstbewusst
  falsch („Server hat eine Obergrenze") → eindeutige, selbsterklärende Rückmeldetexte.
- Bei MCP-Eintrag „Connection timed out after 10s" direkt nach Start: einmal ↻ – Sonde war
  noch nicht bereit. curl über `/cors-proxy` liefert `Invalid Content-Type: text/plain`
  auch für 8787 – als Test ungeeignet.
- Offen: iPad über `.ts.net` (Schritt 5) nicht gemessen.
