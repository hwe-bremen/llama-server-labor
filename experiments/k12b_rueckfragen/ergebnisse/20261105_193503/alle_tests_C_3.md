<!-- alle_tests Variante C Wiederholung 3: 9.3 s, prompt 3948, antwort 441, Form: ok -->

F1: Sollen die Tests nur auf syntaktische Korrektheit (ladbar, korrekte `unittest`-Struktur, keine Syntaxfehler) geprüft werden, oder muss auch die semantische Integrität sichergestellt sein (d. h. der Test-Code darf keine Imports von nicht-existenten Modulen enthalten und muss sich gegen die aktuelle Codebasis auflösen lassen)?
  Optionen: A) Nur Syntax/Struktur (schnell, robust gegen fehlende Dependencies) | B) Syntax + Semantik/Import-Auflösung (streng, findet echte Fehler früher)
  Warum: Bei A reicht `ast.parse` oder ein simpler Importversuch ohne Ausführung. Bei B muss die Testumgebung so konfiguriert sein, dass alle Abhängigkeiten der Tests aufgelöst werden können, was die Komplexität der Umsetzung und die Fehleranfälligkeit bei fehlenden externen Paketen erhöht.

F2: Wie soll das Skript mit Testdateien umgehen, die bereits existieren, aber keine `unittest`-Tests enthalten (z. B. reines Hilfscode oder alte Skripte)?
  Optionen: A) Ignorieren (nur Dateien mit mindestens einem Test prüfen) | B) Fehler melden (Exit 1, da sie im Tests-Ordner liegen sollten)
  Warum: Bei A ist die Prüfung flexibler gegenüber bestehenden Verzeichnisstrukturen. Bei B erzwingt das Skript eine saubere Trennung, zwingt aber zur Bereinigung des Repos vor dem ersten Lauf.

F3: Soll das Skript auch prüfen, ob die Test-IDs in den Testmethoden den Konventionen entsprechen (z. B. `test_...`), oder nur, ob sie existieren?
  Optionen: A) Nur Existenz prüfen | B) Auch Namenskonvention prüfen (z. B. Regex `test_.*`)
  Warum: Bei B muss die Spec die genaue Regex definieren und die Umsetzung implementieren. Bei A wird nur geprüft, ob `unittest` die Tests überhaupt findet.

Annahmen:
- keine
