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

Lesart: Zeigt die UI nach **Y s** einen Fehler, der Server meldet aber `ok` nach X > Y s,
dann hat ein Glied **vor** der Sonde aufgegeben (Server merkt Client-Abbrüche nicht –
im Test nachgewiesen). `abgebrochen` im Log hieße: die Verbindung wurde aktiv gekappt.
Fehlertext der UI wörtlich notieren – er verrät meist, welches Glied es war.
