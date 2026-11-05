<!-- git_schutz Variante C Wiederholung 2: 6.6 s, prompt 3991, antwort 299, Form: ok -->

F1: Sollen die Schreibbereich-Prüfungen auch `.git/config` und `.git/hooks/` explizit in die „Nicht-Ziele“ oder als „geschützte Pfade“ in die Spec aufgenommen werden, oder reicht es, wenn der Umsetzer diese Pfade generell von der automatischen Änderung ausschließt (ohne dass dies in der Spec als separates Ziel formuliert wird)?
  Optionen: A) Ja, explizit in die Spec aufnehmen (als Schutzmechanismus oder Nicht-Ziel) | B) Nein, der Umsetzer soll diese Pfade nur intern ausschließen, ohne Spec-Änderung
  Warum: Bei A muss die Spec den Schutzmechanismus oder die Ausnahme definieren; bei B bleibt die Spec auf das eigentliche Werkzeug fokussiert, der Schutz ist Implementierungsdetail.

F2: Soll der Umsetzer nur das Schreiben in `.git/config` und `.git/hooks/` verhindern, oder auch das Lesen oder Analysieren dieser Dateien, wenn sie im Schreibbereich liegen (um zu vermeiden, dass der Agent Inhalte liest und dann versehentlich ändert)?
  Optionen: A) Nur Schreiben verhindern | B) Lesen und Schreiben verhindern
  Warum: Bei B müsste die Spec klären, ob der Agent diese Dateien ignoriert; bei A ist die Prüfung einfacher (nur auf Write-Operationen/Datei-Ziel prüfen).

Annahmen:
- keine
