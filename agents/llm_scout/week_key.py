#!/usr/bin/env python3
"""
Gemeinsame Funktion fuer den ISO-Kalenderwochen-Schluessel im Dateinamen.

Sowohl llm_scout.py (Erzeuger) als auch send_scout_email.py (Sucher)
nutzen diese Funktion, um fuer ein gegebenes Datum denselben
Berichtsdateinamen zu berechnen. Das verhindert Inkonsistenzen
um den ISO-Jahreswechsel herum (z. B. 28.12.2026 gehoert zur KW 1/2027).
"""

from datetime import datetime


def week_key_for_filename(dt: datetime) -> str:
    """
    Bildet den Dateinamen fuer einen Wochenbericht aus einem datetime-Objekt.

    Nutzt isocalendar() fuer ISO-Jahr und ISO-Kalenderwoche.
    Beispiel: 28.12.2026 -> "llm_scout_kw1_2027.md"
              29.12.2026 -> "llm_scout_kw1_2027.md"
              30.12.2026 -> "llm_scout_kw1_2027.md"
              31.12.2026 -> "llm_scout_kw1_2027.md"

    Args:
        dt: Ein datetime-Objekt (naiv oder bewusst, muss ein gueltiges Datum sein).

    Returns:
        Der Dateiname als String, z. B. "llm_scout_kw1_2027.md".
    """
    iso_year, iso_week, _ = dt.isocalendar()
    return f"llm_scout_kw{iso_week}_{iso_year}.md"
