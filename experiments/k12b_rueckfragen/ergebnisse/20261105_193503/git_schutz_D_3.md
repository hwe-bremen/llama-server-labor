<!-- git_schutz Variante D Wiederholung 3: 15.1 s, prompt 8421, antwort 413, Form: ok -->

F1: Sollen Tests, die das Verhalten von `git`-Aufrufen oder die Unveränderbarkeit von `.git/config` prüfen, die echten Git-Werkzeuge (`git`-Binary im Pfad) verwenden oder gegen einen gemockerten `subprocess`/`os.system`-Pfad geschrieben werden?
  Optionen: Echte Git-Binaries (mit technischer Sperre für Außenwirkung) | Mocking von subprocess/os.system
  Warum: Bei echten Binaries muss eine technische Sperre (R04) definiert werden, die verhindert, dass echte Repos verändert werden. Beim Mocking entfällt diese, aber der Test prüft nur die interne Logik, nicht das tatsächliche Zusammenspiel mit Git (R14).

F2: Muss der Schutzmechanismus verhindern, dass `.git/config` überschrieben wird, oder reicht es, Änderungen daran zu detektieren und den Lauf mit Fehler zu beenden?
  Optionen: Prävention (Schreibschutz/Check vor jedem Write) | Detektion (Check am Ende/Before-Commit)
  Warum: Prävention erfordert tiefere Eingriffe in die Schreibroutinen (z. B. Wrapper um `open` oder `write`), Detektion ist eine nachgelagerte Prüfung. Dies bestimmt den Umfang der Umsetzung und die Komplexität der Tests.

F3: Sollen auch `.git/hooks/` explizit in den Schreibbereich-Schutz einbezogen werden, oder reicht der Schutz der Konfigurationsdatei `.git/config`?
  Optionen: Nur `.git/config` | `.git/config` und `.git/hooks/`
  Warum: Hawes Anlass nennt explizit beide. Wenn Hooks ausgeschlossen werden, muss dies in den Nicht-Zielen oder der Spec klar abgegrenzt werden. Hooks sind oft Skripte, was die Prüfung auf „unbemerkte Änderungen" anders gestaltet als bei einer Konfigurationsdatei.

Annahmen:
- keine
