<!-- 15.6 s, prompt 6804, antwort 786, Form: ok -->

F1: Soll „Größe samt Änderungsstellen gegen R59“ explizit auch die Zeilenanzahl der Anforderungs- und Testplan-Abschnitte separat prüfen, oder reicht die Gesamtgröße der Spec-Datei?
  Optionen: A) Nur Gesamtgröße der Spec-Datei (einfacher, weniger Rauschen) | B) Separate Zählung für Anforderungen und Testplan (präziser, aber komplexer)
  Warum: Bestimmt, ob die Mechanik mehrere Regex-Parse-Runs benötigt oder nur eine Zeilenanzahl der gesamten Datei zählt. Da R59 vorläufig ist und als Hinweis gilt, reicht A meist; B ist nur nötig, wenn Hawe spezifische Limits pro Abschnitt hat.

Annahmen:
- Die Prüfung der „wörtlichen Platzhalter“ erfolgt durch Regex-Muster, die die Vorlage-Zeilen exakt matchen (inkl. Markdown-Syntax wie `**Datum:**`), ohne den Inhalt zu validieren (außer auf Nicht-Leerheit bei Pflichtfeldern).
- „Änderungsstellen“ wird als neuer Pflichtabschnitt „## Änderungsstellen“ in der Vorlage interpretiert, der vor „## Vorgabe-Tests“ steht.
- „Stelle je Anforderung“ bedeutet: Jeder `### A1:`-Block muss ein `- **Stelle:**` enthalten.
- „Prüft je Test mit Unterpunkten“ bedeutet: Jeder `### T1:`-Block muss ein `- **Prüft:**` enthalten, das mindestens eine ID (z.B. `A1`) oder einen Fall nennt.
- „Trockenlauf an git_schutz“ bedeutet: Der Befehl darf keine Dateien im git-geschützten Bereich (`role-split/kette/`, `docs/`, etc.) schreiben oder lesen, die nicht explizit als Eingabe erlaubt sind. Er liest nur die Spec-Datei und die Vorlage.

Quellen:
- `role-split/kette/kette.py` def ablage – wofür (Pfad zur Spec-Datei finden)
- `role-split/kette/kette.py` def abschnitt – wofür (Abschnitte aus Spec-Text extrahieren)
- `role-split/kette/kette.py` def pruefen – wofür (Bestehende Prüflogik als Referenz für Struktur)
- `role-split/kette/kette.py` def _schreibbereich – wofür (Verständnis, was git_schutz schützt)
- `role-split/kette/kette.py` def gegenprobe – wofür (Referenz für Exit-Codes und Mechanik)
- `role-split/kette/kette.py` def main – wofür (Neuen Subcommand `spec-pruefen` einbinden)
- `role-split/kette/kette.py` def _bloecke – wofür (Helfer zum Parsen von Markdown-Blöcken)
- `role-split/kette/kette.py` def _protokoll – wofür (Falls Ausgabe in Datei geschrieben wird)
- `role-split/kette/kette.py` def _datum_aus – wofür (Datum für Ausgabedatei ermitteln)
- `docs/projekt_management/_vorlage_spec.md` – wofür (Exakte Vorlage für Pflichtabschnitte und Platzhalter)
- `role-split/kette/automatik.py` def groesse – wofür (Referenz für Größenberechnung, falls wiederverwendbar)
- `role-split/kette/kette.py` GIT_SCHUTZ – wofür (Konstante für geschützte Pfade)
