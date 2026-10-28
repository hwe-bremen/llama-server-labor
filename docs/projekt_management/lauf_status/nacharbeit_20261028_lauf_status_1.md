# Nacharbeit 1: lauf_status

Zwei Abweichungen von der Spec in `role-split/kette/automatik.py`. Die Vorgabe-Tests sind dafür ergänzt (T7, schon committet); ändere die Testdatei nicht.

1. **C3 – Review-Wert `UNVOLLSTÄNDIG`:** `stand()` sucht nach `**UNVOLLSTAENDIG**` (ohne Umlaut). `review-auto` schreibt in `gesamt_*` aber `**UNVOLLSTÄNDIG**` mit Ä. Suche nach `PASS`, `NACHBESSERN`, `UNVOLLSTÄNDIG` genau wie in der Spec geschrieben.
2. **C4 – Zeile `Spec:`:** Dort steht der ganze Pfad. Die Spec verlangt den Dateinamen (`spec_<datum>_<kt>.md`), z. B. über `Path(...).name`; sonst `fehlt`.

Sonst nichts ändern. Danach `python3 -m unittest -v tests/test_lauf_status.py` – alle 8 grün.
