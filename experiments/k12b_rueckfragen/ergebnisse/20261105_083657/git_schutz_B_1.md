<!-- git_schutz Variante B Wiederholung 1: 16.3 s, prompt 5456, antwort 467, Form: ok -->

F1: Sollen Änderungen an `.git/config` auch dann blockiert werden, wenn sie nur temporär innerhalb einer Session erfolgen (z. B. durch ein Hook-Skript, das kurzzeitig `user.name` setzt und dann zurücksetzt), oder nur, wenn der finale Zustand der Datei vom ursprünglichen Zustand abweicht?
  Optionen: Immer blockieren (präventiv) | Nur blockieren, wenn der finale Zustand geändert ist (zustandsbasiert)
  Warum: Dies entscheidet über die Implementierung der Prüflogik: Muss der Umsetzer den Zustand vor und nach jedem Befehl vergleichen (aufwendiger, sicherer) oder nur den Endzustand gegen ein Referenz-Commit prüfen (einfacher, aber riskanter, wenn Hooks zwischendurch schreiben)?

F2: Welche Dateien unter `.git/hooks/` sollen explizit überwacht werden: Nur Skriptdateien (`.sh`, `.py`, etc.) oder auch alle Dateien, die als Hook konfiguriert sein könnten (inklusive unsichtbarer oder nicht-ausführbarer Dateien)?
  Optionen: Nur ausführbare Skriptdateien | Alle Dateien im Verzeichnis | Nur Dateien, die in `core.hooksPath` oder global konfiguriert sind
  Warum: Dies bestimmt den Suchbereich der Umsetzung. Eine Überprüfung aller Dateien ist robuster gegen Tricks (z. B. Umbenennen von `.sh` zu `config`), erhöht aber den Implementierungsaufwand und das Risiko von False Positives bei nicht-Hook-Dateien.

Annahmen:
- Die Prüfung soll durch ein Git-Hook-Skript (oder eine Wrapper-Funktion) realisiert werden, das vor jedem `commit` oder `push` ausgeführt wird.
- Der „ursprüngliche Zustand" bezieht sich auf den Inhalt von `.git/config` beim Start der Kette/Session (gemessen via `git config` oder Datei-Hash).
- Es gibt keine Anforderung, Änderungen an `.git/hooks/` zu loggen oder zu erlauben, wenn sie explizit von einem autorisierten Skript stammen (da Autorisierung im Kontext „35B darf nichts unbemerkt ändern" nicht greift).
