<!-- git_schutz Variante B Wiederholung 2: 10.8 s, prompt 5456, antwort 516, Form: ok -->

F1: Soll die Prüfung der Schreibbereichs-Regeln auch `.git/config` und `.git/hooks/` explizit als „verbotene“ Pfade aufführen oder diese nur implizit über die Regel „Änderungen nur in den im Auftrag genannten Dateien“ abdecken?
  Optionen: Explizite Whitelist der geschützten Pfade in der Spec | Implizite Abdeckung über die „nur genannte Dateien“-Regel
  Warum: Eine explizite Nennung macht die Testfälle deterministischer (klarer Fehlerpfad), während die implizite Abdeckung flexibler ist, aber die Testkonstruktion erschwert (muss prüfen, dass diese Dateien *nicht* im Diff sind, statt gegen einen expliziten Pfad zu prüfen).

F2: Sollen bestehende Mechanismen zur Schutz der Git-Integrität (z. B. Pre-commit-Hooks oder Skript-Prüfungen) erweitert werden, oder wird ein neuer, isolierter Mechanismus innerhalb des `kette.py`-Workflows implementiert, der vor dem Commit prüft?
  Optionen: Erweiterung bestehender Hooks | Neuer, isolierter Mechanismus in `kette.py`
  Warum: Dies bestimmt den Umfang der zu schreibenden Dateien und die Architektur der Umsetzung. Eine Erweiterung erfordert Änderungen an bestehenden Hook-Dateien, ein neuer Mechanismus erfordert neue Funktionen in `kette.py`.

F3: Soll die Prüfung auch `.gitattributes` und `.gitignore` abdecken, da diese Dateien das Verhalten von Git und damit potenziell auch die Sichtbarkeit von Änderungen beeinflussen können?
  Optionen: Ja, explizit einschließen | Nein, nur `.git/config` und `.git/hooks/`
  Warum: Die Aufgabenstellung nennt explizit nur config und hooks. Eine Ausweitung würde den Scope erhöhen und neue Testfälle erfordern; eine Beschränkung hält die Aufgabe klein und fokussiert.

Annahmen:
- Die Umsetzung erfolgt ausschließlich durch Änderung von Dateien im `llama-server`-Repo, spezifisch im Bereich der Kette (`role-split/kette/` oder `kette.py`), ohne Eingriff in globale Git-Konfigurationen des Benutzers.
- Die „Schreibbereich-Prüfung“ ist ein bereits existierender Mechanismus im Workflow, der erweitert oder neu implementiert wird, um die Integrität der Git-Referenzdaten zu wahren.
