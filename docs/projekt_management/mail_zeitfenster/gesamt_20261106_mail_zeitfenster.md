# Gesamtbefund: mail_zeitfenster

Mechanisch zusammengeführt mit `kette.py zusammenfuehren` (2026-11-07 11:19). Kein Befund wurde weggelassen oder umformuliert.

## Ergebnis

**NACHBESSERN** – Regel: ein hoher Befund in irgendeinem Lauf ergibt NACHBESSERN.

| Lauf | Ergebnis des Laufs |
|---|---|
| `verdict_20261106_mail_zeitfenster_qwen36-35b.md` | NACHBESSERN |
| `verdict_20261106_mail_zeitfenster_qwen36-35b_betrieb.md` | PASS |

## Befunde (alle Läufe)

| Lauf | Schwere | hoch nach Regel | Fundstelle | Befund |
|---|---|---|---|---|
| `verdict_20261106_mail_zeitfenster_qwen36-35b.md` | hoch | ja | `mail_planung.py:890-900` | A3: `get_imap_password` RuntimeError nicht abgefangen |
| `verdict_20261106_mail_zeitfenster_qwen36-35b.md` | niedrig | ja | `mail_planung.py:325-330` | Log-Zeile zaehlt falsch |
| `verdict_20261106_mail_zeitfenster_qwen36-35b_betrieb.md` | niedrig | nein | `mail_planung.py:275` | **Geringe Redundanz:** `import email` ist lazy importiert, wird aber auch in der Schleife verwendet. Da `email` ein Standardmodul ist, ist der Overhead minimal. |
| `verdict_20261106_mail_zeitfenster_qwen36-35b_betrieb.md` | niedrig | nein | `mail_planung.py:315` | **Logik-Check:** `rest` wird inkrementiert, wenn `max_anzahl` erreicht ist. Die Ausgabe zeigt `rest` als „beim nächsten Lauf". Das ist korrekt. |
