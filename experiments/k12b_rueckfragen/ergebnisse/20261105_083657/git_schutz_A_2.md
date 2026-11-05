<!-- git_schutz Variante A Wiederholung 2: 8.1 s, prompt 449, antwort 404, Form: ok -->

F1: Soll die Prüfung nur explizite Änderungen an `.git/config` (z. B. durch `git config`) und `.git/hooks/` (z. B. durch `git init` oder Hook-Skripte) erfassen, oder auch indirekte Änderungen, die durch andere git-Operationen (wie `git commit` oder `git merge`) entstehen, die diese Dateien im Hintergrund modifizieren?
  Optionen: <Nur explizite Änderungen> | <Alle Änderungen, die zum Status führen>
  Warum: Legt fest, ob die Spec nur die direkten API-Aufrufe/Dateizugriffe tracken muss (einfacher) oder den gesamten Git-Workflow-Status gegen einen Snapshot vor der Operation prüft (komplexer, aber sicherer).

F2: Wie soll das System reagieren, wenn eine verbotene Änderung an `.git/config` oder `.git/hooks/` erkannt wird?
  Optionen: <Abbruch der Operation (Exit Code != 0)> | <Warnung, aber Fortsetzung>
  Warum: Bestimmt die Implementierung der Fehlerbehandlung und die Erwartungshaltung der Tests (ob auf Fehlercode oder nur auf Log-Ausgabe geprüft wird).

F3: Sollen Änderungen an `.git/HEAD` oder `.git/refs/` als verbotene Änderungen an `.git/config` oder `.git/hooks/` gewertet werden, oder sind diese explizit erlaubt/neutral?
  Optionen: <Strenge Filterung nur auf config/hooks> | <Erweiterter Filter auf gesamte .git-Struktur außer allowed>
  Warum: Klärt den Umfang der "Schreibbereich-Prüfung". Wenn nur config/hooks gesperrt sind, müssen Tests prüfen, ob refs/änderungen durchgehen. Wenn das gesamte .git-Verzeichnis geschützt ist (außer Temp), ist die Logik anders.

Annahmen:
- keine
