<!-- 6.4 s, prompt 6733, antwort 312, Form: ok -->

F1: Soll die Prüfung explizit auch `.git/HEAD` und `.git/index` (die Hauptdatenbanken des Repos) abdecken, oder nur die drei genannten Bereiche (`config`, `hooks/`, `info/`) schützen?
  Optionen: Nur die drei genannten Bereiche (wie in Hawes Antwort) | Plus HEAD und index (als kritische Kern-Dateien) | Plus alle Unterverzeichnisse von `.git/` (um Lücken zu schließen)
  Warum: Die Antwort nennt explizit `config`, `hooks/` und `info/` und schließt „das ganze Git-Verzeichnis“ aus. `HEAD` und `index` sind jedoch die primären Referenzen und Datenstrukturen; wenn sie unbemerkt geändert werden, ist das Repo inkonsistent. Eine Entscheidung hier definiert den Schutzumfang gegen Datenverlust vs. reine Konfigurations-Integrität.

Annahmen:
- keine

Quellen:
- `role-split/kette/kette.py` def _schreibbereich – wie der Schreibbereich aktuell geprüft wird
- `role-split/kette/kette.py` def _ist_vorgabe – um sicherzustellen, dass die neuen Prüfungen nicht gegen die Vorgabe-Tests verstoßen
- `role-split/kette/kette.py` def gegenprobe – wie die Gegenprobe funktioniert (wichtig für die Test-Strategie)
- `docs/projekt_management/_vorlage_spec.md` – Struktur der Spec
