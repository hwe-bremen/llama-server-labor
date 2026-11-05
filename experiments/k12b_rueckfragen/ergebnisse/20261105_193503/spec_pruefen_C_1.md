<!-- spec_pruefen Variante C Wiederholung 1: 13.1 s, prompt 3986, antwort 422, Form: ok -->

F1: Soll `spec-pruefen` den Schreibbereich auf strikte Existenz und Pfadformate prüfen, oder auch darauf, dass die genannten Dateien/Ordner aktuell im Repo enthalten sind (was bei `git status` von Hand variieren kann)?
  Optionen: A) Nur Format/Existenz der Pfade (robust gegen uncommitte Änderungen) | B) Pfade müssen im aktuellen Git-Index/Working Tree existieren (strenger, aber fehleranfällig bei Worktrees)
  Warum: Ändert die Implementierung der Pfadprüfung und das Risiko von Fehlalarmen, wenn Hawe die Spec schreibt, aber noch nicht committet hat.

F2: Darf `spec-pruefen` Warnungen ausgeben, wenn der Abschnitt „Fehlerpfade“ leer ist oder nur Platzhalter-Text enthält, oder muss er dafür strikt rot (Exit 1) gehen?
  Optionen: A) Warnung (Exit 0), aber Protokollierung | B) Fehler (Exit 1), da unvollständig
  Warum: Bestimmt das Verhalten bei Specs, die noch im Entwurf sind, und ob Hawe die Spec sofort verwerfen muss oder nur korrigieren lassen muss.

F3: Soll `spec-pruefen` prüfen, ob jede Zeile im Abschnitt „Quellen“ auch tatsächlich eine gültige Referenz auf eine Datei im Repo ist (Format `pfad/datei.py Zeilen a-b`), oder reicht die Prüfung, dass der Abschnitt existiert und strukturiert ist?
  Optionen: A) Strenge Validierung der Referenzen (muss existieren) | B) Nur strukturelle Prüfung (Format der Zeilen)
  Warum: Bei A) bricht der Lauf ab, wenn eine Quelle falsch geschrieben ist (früher Fehler). Bei B) wird die Quelle später von `kette.py quellen` geprüft, was zu späteren Fehlern führt.

Annahmen:
- keine
