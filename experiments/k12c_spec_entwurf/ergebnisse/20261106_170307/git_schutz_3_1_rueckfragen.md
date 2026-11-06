<!-- 9.4 s, prompt 6733, antwort 467, Form: ok -->

F1: Soll die Prüfung alle Änderungen an den geschützten Pfaden erfassen, auch wenn sie durch andere, erlaubte Tools (z. B. ein externes `git`-Kommando, das `info/exclude` aktualisiert) verursacht wurden, oder nur direkte Änderungen durch den Umsetzer-Agenten?
  Optionen: Alle Änderungen (Audit-Modus) | Nur direkte Änderungen durch den Agenten (Diff-Modus)
  Warum: Bei „Alle Änderungen“ muss die Gegenprobe sicherstellen, dass der alte Code keine externen Trigger hat, die den Pfad ändern. Bei „Nur direkte Änderungen“ muss die Umsetzung den Zugriff blockieren oder die Änderung rückgängig machen, sonst ist ein externer Trigger ein falscher Positiv-Befund in der Gegenprobe.

Annahmen:
- keine

Quellen:
- `role-split/kette/kette.py` def _bloecke – Parsen der Spec-Struktur für Schreibbereich und Anforderungen
- `role-split/kette/kette.py` def _diff – Erzeugen des Diffs für das Review-Paket
- `role-split/kette/kette.py` def _ist_vorgabe – Prüfen, ob eine Datei Teil der Vorgabe ist
- `role-split/kette/kette.py` def _aenderungen – Ermitteln der geänderten Dateien im aktuellen Stand
- `role-split/kette/kette.py` def gegenprobe – Logik zum Zurücksetzen und Testen
- `role-split/kette/kette.py` def pruefen – Hauptlogik für Prüfung und Gegenprobe
- `role-split/kette/kette.py` def paket – Zusammenstellen des Review-Pakets
- `role-split/kette/kette.py` def urteil – Ableiten des Urteils aus dem Verdikt
- `role-split/kette/automatik.py` def stand – Ermitteln des Projektstands
- `role-split/kette/einsortieren.py` def zuordnen – Zuordnen von Dateien zu Ketten
- `role-split/kette/kette.py` def _git – Aufruf von Git-Befehlen
- `role-split/kette/kette.py` def _rel – Pfadkonvertierung
