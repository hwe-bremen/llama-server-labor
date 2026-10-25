# Gesamtbefund: mail_server_test

Mechanisch zusammengeführt mit `kette.py zusammenfuehren` (2026-10-25 17:49). Kein Befund wurde weggelassen oder umformuliert.

## Ergebnis

**NACHBESSERN** – Regel: ein hoher Befund in irgendeinem Lauf ergibt NACHBESSERN.

| Lauf | Ergebnis des Laufs |
|---|---|
| `verdict_20261023_mail_server_test_qwen36-35b_2.md` | NACHBESSERN |
| `verdict_20261023_mail_server_test_qwen36-35b_betrieb_2.md` | NACHBESSERN |

## Befunde (alle Läufe)

| Lauf | Schwere | hoch nach Regel | Fundstelle | Befund |
|---|---|---|---|---|
| `verdict_20261023_mail_server_test_qwen36-35b_2.md` | hoch | ja | `agents/mail_planung/mail_planung.py` | A4/A5 nicht umgesetzt |
| `verdict_20261023_mail_server_test_qwen36-35b_2.md` | hoch | ja | `tests/test_mail_server_test.py` | A17 nicht umgesetzt |
| `verdict_20261023_mail_server_test_qwen36-35b_2.md` | mittel | ja | `tests/mail_server_test/pruefen.py` | A8-A16 ungetestet |
| `verdict_20261023_mail_server_test_qwen36-35b_betrieb_2.md` | hoch | ja | `mail_planung.py` | Verstoß gegen A4/A5 |
| `verdict_20261023_mail_server_test_qwen36-35b_betrieb_2.md` | mittel | ja | `tests/test_mail_server_test.py` | Unvollständige Testabdeckung |
| `verdict_20261023_mail_server_test_qwen36-35b_betrieb_2.md` | niedrig | ja | `tests/test_mail_server_test.py` | E2E-Test nicht automatisiert |
