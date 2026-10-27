<!-- Schritt 2 automatisch: kette.py umsetzung-auto, Agent „umsetzung_nacht", opencode run ohne TUI. Rücksetzpunkt = Commit „Spec <kurztitel>". -->
Setz docs/projekt_management/spec_{datum}_{kurztitel}.md um. Niemand ist anwesend: keine Rückfragen, kein Warten auf Freigabe.

Pflichtlektüre vor der ersten Änderung: docs/learnings/LERNREGELN.md, Abschnitte „Umsetzung" und „Tests".

Lies keine großen Dateien ganz. Erst search_files bzw. grep (liefert Zeilennummern), dann read mit Zeilenbereich. Die Spec nennt die Fundstellen unter „Quellen". Große Dateien (z. B. role-split/kette/kette.py) änderst du nur gezielt (edit), nie durch Neuschreiben der ganzen Datei.

Konstanten, Formate, Schnittstellen und Optionen nimmst du ausschließlich aus {quellen} und dem Code selbst, nie aus dem Gedächtnis. Fehlt dort etwas, setz nichts Erfundenes ein, sondern nenne es im Handover unter „Abweichungen".
Verbindliche Vorgabe ist {anforderung}. Widerspricht die Spec ihr an einer Stelle, setzt du die Spec um und nennst den Widerspruch im Handover unter „Abweichungen".

- Rücksetzpunkt ist Commit {commit}; nicht selbst committen, kein git reset/checkout/restore/stash.
- Du änderst nur Dateien aus dem Abschnitt „## Schreibbereich" der Spec, dazu tests/test_{kurztitel}.py und den Handover. Alles andere meldet das Werkzeug danach als Verstoß.
- Die Tests der Spec schreibst du als tests/test_{kurztitel}.py (unittest), je Test-ID eine Methode test_<id>_… (z. B. test_t1_timeout), Testtitel und Nummern exakt wie in der Spec. Kein Test darf Außenwirkung haben: keine echten Server außer 127.0.0.1, keine echten Datenordner und kein echtes Repo (immer temporäres Verzeichnis), kein echter Versand.
- Ein Test, der sich nicht wie in der Spec bauen lässt, wird NICHT durch einen anderen ersetzt: unter „Abweichungen" und „Nicht getestet" nennen.
- Befehle mit Außenwirkung führst du nie aus. Nenne sie im Handover unter „Hawe muss ausführen".
- Nach jeder Datei: python3 -m py_compile bzw. bash -n.
- Handover nach docs/projekt_management/handover_{datum}_{kurztitel}.md, Vorlage docs/projekt_management/_vorlage_handover.md. Testtitel exakt wie in der Spec, darunter die echte Ausgabe von python3 -m unittest -v tests/test_{kurztitel}.py.
