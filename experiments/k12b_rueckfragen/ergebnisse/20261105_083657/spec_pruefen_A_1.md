<!-- spec_pruefen Variante A Wiederholung 1: 8.8 s, prompt 439, antwort 440, Form: ok -->

F1: Welche spezifischen syntaktischen und semantischen Regeln sollen in der „mechanischen Prüfung“ der Spec enforced werden?
  Optionen: <Nur strikte YAML-Struktur und existierende Keys> | <Struktur + Typ-Checks der Werte (z.B. Boolean, String)> | <Struktur + Typ-Checks + Referenzvalidierung (z.B. existierende Test-Namen)>
  Warum: Die Komplexität der Implementierung (Parsing-Bibliothek vs. Regex/Handcode) und die Definition der Vorgabe-Tests hängen direkt davon ab, wie tief die Validierung geht.

F2: Wie soll die Fehlerausgabe bei Verletzungen der Spec-Regeln formatiert sein, um die Integration in `kette.py` zu ermöglichen?
  Optionen: <JSON-Array mit Fehlern und Zeilennummern> | <Strukturierte Textausgabe mit Prefixen> | <Exit-Code nur, keine stdout-Ausgabe>
  Warum: Dies bestimmt die Art der Ausgabe-Parsing-Logik in `kette.py` und die Lesbarkeit der Fehlermeldungen für den Entwickler im Review-Prozess.

F3: Sollen die vorgeschlagenen Vorgabe-Tests (die nach der Spec-Prüfung kommen) explizit in der Spec-Datei selbst definiert werden oder in einer separaten Datei/Struktur?
  Optionen: <In der Spec-Datei als Key> | <Separate YAML/JSON-Datei im gleichen Verzeichnis> | <Feste, harte Kodierung in der Spec-Prüf-Logik>
  Warum: Dies ändert die Struktur der zu validierenden Spec-Datei und damit die Logik der mechanischen Prüfung sowie die Generierung der Tests.

Annahmen:
- Die Spec ist eine YAML-Datei. (Standardannahme für Config/Spec-Dateien in diesem Kontext, da kein anderer Format genannt wurde).
- Der Exit-Code 0 signalisiert Erfolg, ungleich 0 Fehler. (Standardverhalten für CLI-Tools).
