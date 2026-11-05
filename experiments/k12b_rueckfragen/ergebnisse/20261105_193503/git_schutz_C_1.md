<!-- git_schutz Variante C Wiederholung 1: 16.0 s, prompt 3991, antwort 568, Form: ok -->

F1: Sollen Änderungen an `.git/config` (z. B. `user.name`, `user.email`) als Fehler gewertet werden, auch wenn sie technisch korrekt formatiert sind, um „unbeabsichtigte“ Änderungen durch das Modell zu verhindern?
  Optionen: Ja, nur `.git/hooks/` ist gesperrt | Ja, `.git/config` und `.git/hooks/` sind gesperrt | Nein, nur `.git/hooks/` ist gesperrt
  Warum: Legt fest, ob der Schreibbereich in der Spec explizit `.git/config` ausschließt (was die Umsetzung der Schreibbereichs-Prüfung ändert) oder ob die Sperre nur für Hooks gilt.

F2: Soll die Prüfung auf `.git/config` auch dann greifen, wenn die Änderung durch eine explizite Systemkonfiguration des Nutzers erfolgt (z. B. `git config --global` vor dem Commit), oder nur, wenn das Modell die Datei im Rahmen der Aufgabe modifiziert?
  Optionen: Immer prüfen (strenge Sperre) | Nur prüfen, wenn das Modell die Datei im Handover/Diff enthält (kontextabhängig)
  Warum: Bei „Immer prüfen“ muss die Umsetzung den gesamten aktuellen Zustand von `.git/config` laden und gegen einen Referenzzustand prüfen. Bei „Nur im Handover“ reicht ein Diff-Check. Dies ändert die Test-Logik und die Implementierung der Schutzmechanik.

F3: Sollen Änderungen an `.gitattributes` oder `.gitignore` als „unbemerkt“ verboten gelten, da sie das Repository-Verhalten ändern?
  Optionen: Ja, alle `.git/*` sind gesperrt | Nein, nur `.git/config` und `.git/hooks/` sind gesperrt
  Warum: Definiert den Umfang der „Sperre“. Eine breitere Sperre erfordert eine allgemeinere Prüflogik in der Umsetzung.

Annahmen:
- Die „unbemerkt“ Bedingung bezieht sich darauf, dass der Reviewer (oder das automatische System) die Änderung in den Prüfdokumenten nicht explizit als genehmigt oder bekannt markiert findet, bevor sie committet werden.
- Die Umsetzung muss sicherstellen, dass keine dieser Dateien im finalen Commit-Status von dem im Anforderungs-Dokument definierten Zustand abweicht, es sei denn, dies ist explizit Teil der Aufgabe (was hier nicht der Fall ist).
- Vermutung: `.git/hooks/` gilt als gesperrt, weil dort Skripte abgelegt werden können, die bei jedem Git-Event ausgeführt werden (Risiko für unerwünschte Aktionen).
