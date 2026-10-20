<!-- Schritt 2, OpenCode, Agent „umsetzung" (Tab). Rücksetzpunkt = aktueller Commit. -->
Setz docs/projekt_management/spec_{datum}_{kurztitel}.md um.

Verbindliche Vorgabe ist {anforderung}. Widerspricht die Spec ihr an einer Stelle, setzt du die Spec um und nennst den Widerspruch im Handover unter „Abweichungen".

- Rücksetzpunkt ist Commit {commit}; nicht selbst committen.
- Die Tests der Spec schreibst du als tests/test_{kurztitel}.py (unittest), je Test-ID eine Methode test_<id>_… (z. B. test_t1_timeout). Kein Test darf Außenwirkung haben: keine echten Server außer 127.0.0.1, keine echten Datenordner (immer temporäres Verzeichnis), kein echter Versand.
- Ein Test, der sich nicht wie in der Spec bauen lässt, wird NICHT durch einen anderen ersetzt: unter „Abweichungen" und „Nicht getestet" nennen.
- Befehle mit Außenwirkung führst du nie aus, auch nicht nach Freigabe. Nenne sie im Handover unter „Hawe muss ausführen".
- Nach jeder Datei: python3 -m py_compile bzw. bash -n.
- Handover nach docs/projekt_management/handover_{datum}_{kurztitel}.md, Vorlage _vorlage_handover.md. Testtitel exakt wie in der Spec, darunter die echte Ausgabe von python3 -m unittest -v tests/test_{kurztitel}.py.
