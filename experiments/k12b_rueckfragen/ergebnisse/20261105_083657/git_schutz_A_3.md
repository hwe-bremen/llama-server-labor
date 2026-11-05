<!-- git_schutz Variante A Wiederholung 3: 6.1 s, prompt 449, antwort 297, Form: ok -->

F1: Sollen explizite Schreibzugriffe auf `.git/config` und `.git/hooks/` von der Prüfung ausgeschlossen werden, oder müssen alle Schreibzugriffe auf diese Pfade (selbst wenn sie vom Tool selbst stammen) protokolliert und blockiert/erlaubt werden?
  Optionen: A) Alle Schreibzugriffe auf diese Pfade sind verboten und werden als Fehler gewertet | B) Schreibzugriffe durch das Tool selbst sind erlaubt, fremde Schreibzugriffe verboten | C) Alle Schreibzugriffe werden protokolliert, aber nicht blockiert (nur Warnung)
  Warum: Bestimmt die Logik der Prüf-Regeln in der Spec. Option A ist strikt, Option B erfordert die Unterscheidung der Quelle (Tool vs. extern), Option C ändert den Mechanismus von Blockierung zu Protokollierung.

F2: Welche Fehlerkategorie soll bei einem verbotenen Schreibzugriff auf `.git/config` oder `.git/hooks/` ausgelöst werden?
  Optionen: A) Fatal Error (Abbruch der Operation) | B) Warning (Fortsetzung erlaubt, aber Warnung im Log) | C) Soft Error (Fortsetzung erlaubt, kein Log-Eintrag, nur interner Status)
  Warum: Bestimmt das Verhalten des Wrappers/Tools bei Verstoß und damit die Testfälle für die Erfolgsmeldung vs. Fehlerbehandlung.

Annahmen:
- keine
