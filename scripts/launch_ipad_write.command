#!/bin/bash
# iPad-Start im WRITE-Modus (Frontend-Modell darf schreiben/loeschen).
# Duenner Doppelklick-Wrapper um launch_ipad.command write.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$HERE/launch_ipad.command" write
