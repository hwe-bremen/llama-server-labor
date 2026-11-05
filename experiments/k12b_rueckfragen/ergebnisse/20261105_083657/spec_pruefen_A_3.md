<!-- spec_pruefen Variante A Wiederholung 3: 8.6 s, prompt 439, antwort 435, Form: ok -->

F1: Soll „mechanisch prüfen“ ausschließlich syntaktische/strukturelle Integrität (z. B. JSON-Validierung, Vorhandensein von Pflichtfeldern) bedeuten, oder auch semantische Konsistenzprüfungen (z. B. „ist die Spec logisch widerspruchsfrei“)?
  Optionen: Nur Syntax/Struktur | Auch Semantik/Konsistenz
  Warum: Dies bestimmt den Umfang der Prüflogik in `kette.py` und die zu schreibenden Tests (einfache Parser-Tests vs. komplexe Regel-Engines).

F2: Was genau ist mit „Trockenlauf an git_schutz“ gemeint: Eine Simulation, die verhindert, dass Änderungen committed werden, oder eine Prüfung, ob die Spec die Bedingungen von `git_schutz` erfüllt (z. B. keine sensiblen Daten)?
  Optionen: Simuliere Commit-Verhinderung | Prüfe Compliance mit git_schutz-Regeln
  Warum: „An git_schutz“ ist mehrdeutig. Es ändert die Implementierung von `kette.py` grundlegend (Mocking vs. Rule-Checking).

F3: Was bedeutet „alle_tests ohne Fehlalarme“ im Kontext des Trockenlaufs: Die Tests müssen erfolgreich durchlaufen, oder sie müssen sicherstellen, dass keine Warnungen/Fehler bei der Validierung der Spec auftreten?
  Optionen: Tests laufen grün | Keine Warnungen/Errors während der Validierung
  Warum: „Ohne Fehlalarme“ bezieht sich auf das Verhalten des Prüfsystems. Ist es ein Erfolgskriterium für die Spec (sie ist gut) oder für das Tool (es ist robust)?

Annahmen:
- „Mechanisch ohne Modell“ bedeutet Verwendung von deterministischen Regeln und Parsern, keine LLM-Aufrufe.
- „git_schutz“ ist ein existierendes Modul/Tool im Repo, das als Schnittstelle dient.
- „Vorgabe-Tests“ sind Tests, die aus der Spec generiert werden.
