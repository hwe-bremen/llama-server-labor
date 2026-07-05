#!/bin/bash
# Startet das Lab im WRITE-Modus (Frontend-Modell darf schreiben/loeschen).
# Duenner Doppelklick-Wrapper um launch_lab.command write.
HERE="$(cd "$(dirname "$0")" && pwd)"
exec bash "$HERE/launch_lab.command" write
