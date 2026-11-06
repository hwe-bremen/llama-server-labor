<!-- 16.5 s, prompt 6733, antwort 392, Form: ok -->

F1: Was genau zählt als „melden“?
  Optionen: Exit-Code 1 mit Fehlermeldung auf stderr | Exit-Code 1 mit Meldung in eine Log-Datei | Beides (Exit-Code 1 + stderr + Log-Datei)
  Warum: Die Spec muss festlegen, wie der Umsetzer (oder das Tool) die Information erhält, um den Exit-Code 1 auszulösen und die Meldung zu produzieren.

Annahmen:
- keine

Quellen:
- `role-split/kette/kette.py` def umsetzung_auto – wie der Umsetzer aufgerufen wird und was als Exit 1 gilt
- `role-split/kette/kette.py` def _im_schreibbereich – wie der Schreibbereich geprüft wird (hier muss die neue Prüfung integriert werden)
- `role-split/kette/kette.py` def _schreibbereich – wo der Schreibbereich definiert wird
- `role-split/kette/kette.py` def _git – wie Git-Befehle ausgeführt werden (für die Prüfung)
- `role-split/kette/kette.py` def pruefen – wie die Prüfung durchgeführt wird
- `role-split/kette/kette.py` def gegenprobe – wie die Gegenprobe funktioniert (muss auch die neue Prüfung abdecken)
- `tests/test_umsetzung_auto.py` – Tests für den Umsetzungsprozess
- `tests/test_kette_review_auto.py` – Tests für den Review-Prozess
- `tests/test_vorgabe_tests.py` – Struktur der Vorgabe-Tests
- `tests/test_paket_vollstaendig.py` – Struktur des Review-Pakets
- `tests/test_scout_bericht_ueberschreiben.py` – wie Berichte geschrieben werden
- `tests/test_mail_planung.py` – wie Mail-Pläne geprüft werden
