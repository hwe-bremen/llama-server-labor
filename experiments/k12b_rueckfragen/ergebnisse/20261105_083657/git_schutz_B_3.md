<!-- git_schutz Variante B Wiederholung 3: 12.0 s, prompt 5456, antwort 583, Form: ok -->

F1: Sollen Änderungen an `.git/config` (z. B. `user.name`, `user.email`) explizit blockiert werden, oder reicht es, nur Änderungen an `.git/hooks/` und kritischen `.git`-Strukturen (wie `.git/HEAD`, `.git/index`) zu sperren, während `.git/config`-Änderungen nur protokolliert werden?
  Optionen: A) Vollständige Blockade von `.git/config` (wie Hooks) | B) Nur Protokollierung von `.git/config`, Blockade nur für Hooks und kritische Strukturen
  Warum: Dies bestimmt, ob die Spezifikation eine harte `Stop`-Logik für Config-Dateien implementiert oder eine weichere Warn-Logik. Eine Blockade verhindert, dass der 35B seine Identität fälscht; eine Protokollierung erfordert eine andere Review-Logik im Tool.

F2: Soll das Tool bei einem erkannten Verstoss gegen die Schreibbereichsregeln den gesamten `git`-Vorgang (z. B. `commit` oder `push`) abbrechen (Exit-Code ≠ 0), oder soll es den Vorgang nur warnen und fortsetzen, aber den Fehler im Log markieren?
  Optionen: A) Abbruch des Vorgangs (harte Sperre) | B) Warnung und Fortsetzung (weiche Sperre)
  Warum: R20 verlangt, dass Teilerfolg zu Exit ≠ 0 führt, wenn Datenverlust oder Unbemerkt droht. Eine harte Sperre verhindert den Commit direkt; eine weiche Sperre könnte den Commit erlauben, was gegen das Sicherheitsziel verstößt, wenn nicht explizit anders entschieden.

F3: Sollen auch Änderungen an anderen `.git/`-Unterordnern (z. B. `.git/logs/`, `.git/refs/`) blockiert werden, oder ist der Fokus ausschließlich auf `.git/hooks/` und `.git/config`?
  Optionen: A) Nur `.git/hooks/` und `.git/config` | B) Alle `.git/`-Pfade außer explizit erlaubten (wie `.gitignore` im Root)
  Warum: Die Definition des „Schreibbereichs“ muss klar sein. Eine zu weite Definition könnte legitime Git-Interne blockieren; eine zu enge könnte andere Manipulationen (wie Log-Injection) erlauben.

Annahmen:
- Das Tool wird als Pre-Commit-Hook oder in `kette.py` integriert, der vor dem Commit ausgeführt wird.
- Die Prüfung erfolgt auf Basis des `git diff`-Status oder der geplanten Änderungen.
- Es gibt keine expliziten Ausnahmen für bestimmte Branches oder User.
