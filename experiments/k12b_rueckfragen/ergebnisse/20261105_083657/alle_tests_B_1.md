<!-- alle_tests Variante B Wiederholung 1: 14.6 s, prompt 5427, antwort 709, Form: F4 ohne „Optionen:“; F4 ohne „Warum:“ -->

F1: Soll das Skript alle `.py`-Dateien im Ordner `tests/` ausführen oder nur solche, deren Name mit `test_` beginnt oder auf `_test.py` endet?
  Optionen: Alle .py-Dateien in tests/ | Nur Dateien mit `test_`-Präfix oder `_test.py`-Suffix
  Warum: Bestimmt, welche Dateien als „Testdateien" gezählt werden und ob z. B. Hilfsmodule oder Konfigurationsdateien im Testordner fälschlich als Tests interpretiert und ausgeführt werden.

F2: Wie soll das Skript mit Testdateien umgehen, die beim Aufruf nicht sofort mit einem Exit-Code terminieren (z. B. durch blockierende Aufrufe oder Endlosschleifen)?
  Optionen: Zeitlimit (Timeout) für jeden einzelnen Testlauf setzen | Keine Begrenzung, Blockierung führt zum Abbruch des gesamten Skripts
  Warum: R36 verlangt Zeitlimits für Tests mit Servern/Threads. Eine Entscheidung hier verhindert, dass das Skript bei einem hängenden Test unbegrenzt wartet, oder erzwingt manuelle Abbrüche.

F3: Soll das Skript auch nicht-Python-Dateien im `tests/`-Ordner ignorieren oder explizit warnen, falls dort Dateien liegen, die nicht als Python-Skripte ausgeführt werden können?
  Optionen: Ignorieren ohne Warnung | Warnung ausgeben, aber weiterlaufen
  Warum: Bestimmt die Robustheit des Skripts gegenüber unerwarteten Dateien im Testverzeichnis. Eine Warnung hilft bei der Fehlersuche, ein stilles Ignorieren hält die Ausgabe sauber.

Annahmen:
- Das Skript wird im Repository-Root ausgeführt und sucht rekursiv oder nur im obersten Level von `tests/` (Vermutung: nur oberstes Level, da `tests/` oft viele Unterordner hat, aber „alle Testdateien" impliziert oft eine flache Liste; wenn nicht, muss dies geklärt werden. Da dies eine Standardannahme ist, wird hier „nur oberstes Level" als Annahme getroffen, es sei denn, die Spec sagt etwas anderes. *Korrektur*: Da keine Info vorliegt, ist dies eine kritische Frage. Ich werde sie als F4 hinzufügen, um die Reichweite zu klären).
- Das Skript gibt eine Zusammenfassung der Ergebnisse (Anzahl bestanden/fehlgeschlagen) am Ende aus.
- Der Exit-Code des Skripts ist 0, wenn alle Tests bestanden, und ungleich 0, wenn mindestens ein Test fehlschlägt oder das Skript selbst einen Fehler hat.

F4: Sollen Unterordner im `tests/`-Verzeichnis rekursiv durchsucht werden, oder nur Dateien im direkten `tests/`-Ordner?
  Optionen: Rekursiv alle .py-Dateien finden | Nur Dateien im direkten `tests/`-Ordner
  Warum: Bestimmt die Reichweite der Testausführung. Viele Projekte haben Unterordner für verschiedene Testarten (z. B. `tests/unit`, `tests/integration`). Eine falsche Annahme führt dazu, dass Tests nicht gefunden oder unbeabsichtigt ausgeführt werden.
