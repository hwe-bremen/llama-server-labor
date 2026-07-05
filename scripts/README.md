# scripts/

Launcher und Hilfs-/Demo-Skripte.

Geplante Belegung:
- launch_router.command   (macOS-Doppelklick-Starter fuer den Router)
- run_ab.py               (A/B-Vergleich von Modellen)
- tool_demo.py            (Tool-Calling-Demo)

Achtung bei launch_router.command: referenziert models.ini per ABSOLUTEM
Pfad. Wird models.ini nach config/ verschoben, muss der PRESET-Pfad im
Launcher mitgezogen werden.
