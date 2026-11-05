<!-- git_schutz Variante C Wiederholung 3: 5.8 s, prompt 3991, antwort 262, Form: ok -->

F1: Wie soll das Verbot technisch durchgesetzt werden – durch explizite Prüfung der Datei-Inhalte auf verbotene Schlüssel (z. B. `user.name`) oder durch eine globale Sperre aller Änderungen an `.git/config` und `.git/hooks/` unabhängig vom Inhalt?
  Optionen: Inhaltliche Prüfung (nur bestimmte Schlüssel sind verboten) | Globale Sperre (alle Änderungen an diesen Pfaden sind verboten)
  Warum: Bestimmt den Schreibbereich (darf die Umsetzung diese Dateien generell lesen, um sie zu prüfen?) und die Testfälle (muss ein Test prüfen, dass eine erlaubte Änderung an `.git/config` scheitert, oder dass jede Änderung scheitert?).

F2: Sollen Änderungen an `.git/hooks/`, die keine Skripte sind (z. B. reine Textdateien oder Konfigurationsdateien ohne Ausführungsberechtigung), explizit erlaubt sein oder ebenfalls verboten werden?
  Optionen: Alles verboten | Nur ausführbare Skripte (.sh, .py etc.) verboten
  Warum: Beeinflusst die Spezifikation der „Sperre“ und die Implementierung der Prüfung (Dateityp-Erkennung vs. Pfad-Erkennung).

Annahmen:
- keine
