# config/

Konfigurationsdateien.

Geplante Belegung:
- models.ini   (llama.cpp Router-Preset, Sampling-Parameter pro Modell)

Wird models.ini hierher verschoben, an diesen Stellen den Pfad anpassen:
- scripts/launch_router.command  (Variable PRESET, absoluter Pfad)
- ggf. Agenten/Skripte, die models.ini direkt laden
