# scripts/

Launcher und Hilfs-/Demo-Skripte.

Belegung:
- launch_router.command   (macOS-Doppelklick-Starter fuer den Router)
- run_ab.py               (A/B-Vergleich von Modellen)
- tool_demo.py            (Tool-Calling-Demo, liest aus ../sandbox/)

WICHTIG nach dem Verschieben: launch_router.command hat beim Neuschreiben das
Ausfuehr-Bit verloren. Einmalig wieder setzen, sonst ist der Doppelklick tot:

    chmod +x scripts/launch_router.command

Der PRESET-Pfad im Launcher zeigt bereits korrekt auf ../config/models.ini
(absoluter Pfad, wurde bei der Migration angepasst).

Hinweis run_ab.py: schreibt results_ab.md ins aktuelle Arbeitsverzeichnis.
Aus dem Projekt-Root starten (python scripts/run_ab.py), dann landet der
Report im Root.
