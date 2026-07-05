# config/

Konfigurationsdateien.

Belegung:
- models.ini   (llama.cpp Router-Preset, Sampling-Parameter pro Modell)

models.ini wird per absolutem Pfad referenziert von:
- scripts/launch_router.command  (Variable PRESET) — bereits angepasst.

Nach einem llama.cpp-Upgrade kurz testen, ob das INI-Format noch sauber laedt
(curl http://localhost:8080/v1/models zeigt alle Eintraege).
