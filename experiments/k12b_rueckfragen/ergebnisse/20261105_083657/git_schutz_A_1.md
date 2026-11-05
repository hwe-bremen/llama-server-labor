<!-- git_schutz Variante A Wiederholung 1: 11.5 s, prompt 449, antwort 580, Form: ok -->

F1: Sollen Änderungen an `.git/config` als "unbemerkt" gelten, wenn sie durch explizite Konfigurationsbefehle des Nutzers (z. B. `git config user.name ...`) erfolgt sind, oder soll jegliche Modifikation dieser Datei blockiert/protokolliert werden, auch wenn sie vom Nutzer initiiert wurde?
  Optionen: Nur automatische/heimliche Änderungen erkennen (z. B. Hook-Verzicht) | Jegliche Änderung blockieren oder explizit genehmigen lassen | Nur Änderungen an Schlüsseln wie `user.name` und `user.email` blockieren
  Warum: Legt fest, ob die Spec nur das Verhindern von Hook-Interferenzen erfordert (einfacher) oder ein striktes Immutable-Design für die Config-Datei vorsieht (komplexer, mehr Tests für erlaubte/unerlaubte Pfade).

F2: Soll die Prüfung im Pre-Commit-Hook oder im Post-Commit-Hook stattfinden, um festzustellen, dass `.git/config` geändert wurde?
  Optionen: Pre-Commit (vor dem Commit prüfen, ob die Datei im Index/Working Tree geändert ist) | Post-Commit (nach dem Commit prüfen, ob die Datei sich vom vorherigen Zustand unterscheidet) | Staging-Phase-Prüfung (direkt beim `git add`)
  Warum: Bestimmt die technische Umsetzung (welches Git-Event genutzt wird) und die Testfälle (z. B. Test auf veränderte Datei vor Commit vs. Änderung nach Commit).

F3: Wenn eine unerlaubte Änderung an `.git/config` festgestellt wird, soll der Prozess sofort abgebrochen werden (Exit Code != 0) oder nur gewarnt werden (Exit Code 0, aber Warnung in Logs)?
  Optionen: Blockierend (Abbruch) | Warnend (Fortsetzung erlaubt) | Blockierend nur bei kritischen Schlüsseln, warnend bei anderen
  Warum: Ändert die Spec der Fehlerbehandlung und die Erwartungshaltung der Tests (Exit Code vs. Log-Ausgabe).

Annahmen:
- Die Prüfung bezieht sich ausschließlich auf die Datei `.git/config` im Root des Repos, nicht auf andere versteckte Dateien in `.git/`. (Vermutung: Andere `.git/`-Dateien sind weniger kritisch für die "unbemerkt"-Thematik im Kontext von `user.name`.)
- Der "unbemerkt"-Aspekt bezieht sich primär darauf, dass der Nutzer nicht sieht, dass ein Tool/Hook seine Config überschrieben hat. Daher ist ein Pre-Commit-Hook der logischste Ort, um dies zu verhindern, bevor der Commit abgeschlossen ist.
