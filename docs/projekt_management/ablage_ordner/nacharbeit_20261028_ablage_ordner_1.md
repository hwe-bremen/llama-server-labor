# Nacharbeit 1: ablage_ordner

Zwei Abweichungen von der Spec. Die Vorgabe-Tests sind dafür ergänzt (T2, T7; schon committet) – ändere die Testdatei nicht.

1. **E2 – kein Rückfall auf flache Dateien:** `datei_suchen` sucht im Ordner und danach zusätzlich flach in `PM`. Die Spec sagt: Existiert der Ordner, werden flache Dateien derselben Kette nicht mehr gefunden. Entferne in beiden Zweigen (mit und ohne Datum) den Rückfall auf `PM`; gesucht wird nur in `ablage(kurztitel)`.
2. **E4 – Pfade mit Platzhaltern:** `_ablage_text` biegt nur Pfade um, die direkt auf `.md` enden und nur aus `[\w.-]` bestehen. Pfade in den Hand-Prompts wie `docs/projekt_management/verdict_{datum}_{kurztitel}_<modellkürzel>.md` (`prompts/review.md`, `review2.md`, `tief.md`) bleiben dadurch flach. Laut E1 ersetzt `_ablage_text` **jedes** `docs/projekt_management/`, auf das nicht `_vorlage` folgt, durch `_ablage_rel(kurztitel) + "/"` – ohne Bedingung an den Rest des Pfads. Achte darauf, dass dabei kein doppelter Ordner `…/<kt>/<kt>/` entsteht (Text erst umbiegen, dann Platzhalter ersetzen – wie in E4 beschrieben – oder schon umgebogene Pfade auslassen).

Sonst nichts ändern. Danach `python3 -m unittest -v tests/test_ablage_ordner.py` – alle 7 grün.
