<!-- spec_pruefen Variante C Wiederholung 2: 14.6 s, prompt 3986, antwort 721, Form: ok -->

F1: Soll `kette.py spec-pruefen` die Spec-Struktur gegen die Vorlage (`_vorlage_spec.md`) validieren (z. B. Pflichtsektionen, Format von Quellen/Tests) oder nur die in der Spec referenzierten Dateien auf Existenz und syntaktische Korrektheit prüfen?
  Optionen: A) Struktur-Validierung gegen Vorlage (Pflichtfelder, Format) | B) Nur Existenz/Syntax der referenzierten Dateien | C) Beides (Struktur + Dateien)
  Warum: Bestimmt den Umfang des mechanischen Checks. Eine reine Datei-Prüfung ist einfacher, aber eine Struktur-Validierung stellt sicher, dass die Spec den Konventionen der Kette entspricht, bevor Tests geschrieben werden. Hawes Hinweis auf "Trockenlauf an git_schutz" deutet auf Integrität des Repo-Zustands hin, was eher zu B oder C passt, aber "prueft eine Spec" kann auch Inhalt betreffen.

F2: Wie soll `kette.py spec-pruefen` mit fehlenden oder ungültigen Quellen umgehen, die in der Sektion "Quellen" aufgeführt sind?
  Optionen: A) Fehler (Exit 1), wenn eine referenzierte Datei/Zeile nicht existiert | B) Warnung (Exit 0), aber Dokumentation des Fehlers | C) Ignorieren, wenn die Quelle nicht im Repo ist (externe Quelle)
  Warum: Die Vorlage erlaubt externe Quellen unter "Offene Fragen". Wenn eine Quelle in "Quellen" steht, muss geklärt sein, ob sie zwingend im Repo sein muss. Ein strikter Check (A) verhindert Fehler in `kette.py quellen`, ein laxer (B/C) erlaubt unvollständige Specs.

F3: Soll `kette.py spec-pruefen` auch die Konsistenz zwischen "Anforderungen" und "Fehlerpfaden" prüfen (z. B. jede Anforderung hat mindestens einen Fehlerpfad)?
  Optionen: A) Ja, strikte Konsistenzprüfung | B) Nein, nur strukturelle Integrität | C) Ja, aber nur Warnung
  Warum: Dies ist eine logische Prüfung der Spec-Qualität. Wenn die Aufgabe "mechanisch ohne Modell" heißt, ist die Auswertung von Textkonsistenz (A/C) komplexer als reine Dateiprüfung (B). Hawes Fokus auf "Trockenlauf an git_schutz" könnte darauf hindeuten, dass nur Repo-Integrität (B) gemeint ist, aber "prueft eine Spec" schließt auch Logik ein.

F4: Wie soll `kette.py spec-pruefen` mit bestehenden Tests (`tests/test_<kurztitel>.py`) umgehen, wenn die Spec noch keine Tests definiert hat?
  Optionen: A) Fehler, wenn Tests existieren, aber nicht in Spec referenziert | B) Ignorieren, wenn Spec keine Tests hat | C) Warnung, falls Tests existieren, die in Spec nicht geplant sind
  Warum: Die Vorlage erlaubt Vorgabe-Tests. Wenn die Spec noch keine Tests hat, aber Tests im Repo sind, ist das ein Inkonsistenz-Zustand. Die Frage bestimmt, ob der Pruefen-Befehl dies als Fehler oder Hinweis wertet.

Annahmen:
- keine
