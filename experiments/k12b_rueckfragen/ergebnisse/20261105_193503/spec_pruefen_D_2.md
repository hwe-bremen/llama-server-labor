<!-- spec_pruefen Variante D Wiederholung 2: 25.1 s, prompt 8725, antwort 886, Form: ok -->

F1: Soll `spec-pruefen` nur die **Struktur** (Vorhandensein der Pflichtabschnitte, Format der Quellen, Schreibbereich) prüfen, oder auch **inhaltliche Plausibilität** (z. B. „Anforderung A1 ist im Testplan T1 abgedeckt“, „Fehlerpfad-Tabelle enthält Zeilen für jede Anforderung“)?
  Optionen: A) Nur Struktur und Syntax | B) Struktur + inhaltliche Konsistenz (Abdeckung, Referenzen)
  Warum: B) erfordert deutlich komplexere Parsing-Logik in `kette.py` und kann zu falschen Fehlalarmen führen, wenn die Spec-Lücken offen sind. A) ist robust und mechanisch sicher. Da es ein „Trockenlauf“ vor der Umsetzung sein soll, verhindert A) nur syntaktische Brüche, die den weiteren Workflow blockieren.

F2: Wie soll `spec-pruefen` mit **Offenen Fragen** im Abschnitt „Offene Fragen“ umgehen?
  Optionen: A) Sie sind erlaubt, solange sie dokumentiert sind (grüner Check). | B) Sie sind ein Fehler (roter Check), da Spec vor Umsetzung vollständig sein muss. | C) Sie sind erlaubt, aber mit Warnung.
  Warum: R02 verlangt, dass Nicht-Repo-Werte in „Offene Fragen“ landen. Wenn B) gilt, darf keine Spec geschrieben werden, solange externe Infos fehlen. A) oder C) erlauben den Fortlauf der Kette auch bei unvollständiger Info. Die Entscheidung bestimmt, ob `spec-pruefen` als Gatekeeper dient oder nur als Formcheck.

F3: Sollen **Vorgabe-Tests** (der Abschnitt `## Vorgabe-Tests`) mechanisch auf Vollständigkeit geprüft werden (z. B. „Jede Test-ID existiert als Methode in der gelisteten Datei“)?
  Optionen: A) Ja, strikte Prüfung der Methodennamen gegen die Liste. | B) Nein, das übernimmt `tests-pruefen` später. | C) Nur Prüfung, ob der Abschnitt existiert.
  Warum: Wenn A) gilt, muss `spec-pruefen` auch die Testdatei lesen und parsen. Das erhöht die Komplexität und Abhängigkeit von der Testdatei (die noch nicht existieren kann, wenn Tests vor der Umsetzung geschrieben werden? Nein, R48 sagt: Tests vor Umsetzung schreiben). Klärung nötig, ob dieser Schritt Teil der „Spec-Prüfung“ ist oder in `tests-pruefen` verbleibt.

F4: Was ist das **Exit-Verhalten** bei Funden?
  Optionen: A) Exit 1 bei jedem Mangel (Stop). | B) Exit 1 bei kritischen Mängeln (Struktur), Exit 0 mit Warnungen bei geringfügigen. | C) Alle Funde in eine Datei, Exit 0 immer (nur zur Info).
  Warum: `kette.py` nutzt Exit-Codes für die Steuerung. Wenn `spec-pruefen` vor `tests-pruefen` läuft, muss klar sein, ob ein Fehler den gesamten Prozess abbricht oder nur korrigiert werden muss, bevor weitergemacht wird. A) ist sicherer für die Kette.

Annahmen:
- Der Befehl ist `python3 role-split/kette/kette.py spec-pruefen <kurztitel>`.
- „Trockenlauf an git_schutz und alle_tests“ bedeutet, dass die Regeln aus K12 (git_schutz) und K13 (alle_tests) als Referenz für die *Struktur* der Spec dienen, aber nicht, dass `spec-pruefen` den Code dieser anderen Ketten prüft.
- „Mechanisch ohne Modell“ bedeutet: Nur Python-Standardbibliothek, keine LLM-Aufrufe.
- Die Prüfung erfolgt gegen die Datei `docs/projekt_management/anforderung_...md` (Anforderung) und `docs/projekt_management/spec_...md` (Spec), wobei `spec-pruefen` primär die Spec auf Konformität zur Anforderung und interne Konsistenz prüft.
