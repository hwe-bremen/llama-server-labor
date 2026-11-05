<!-- git_schutz Variante D Wiederholung 1: 12.5 s, prompt 8421, antwort 283, Form: ok -->

F1: Sollen Tests explizit prüfen, dass `.git/config` und `.git/hooks/` unverändert bleiben, oder reicht ein generischer Schutz, der alle nicht im Schreibbereich liegenden Pfade (außer explizit erlaubten) sperrt?
  Optionen: Spezifisch (nur .git) | Generisch (alle nicht im Schreibbereich, außer expliziten Ausnahmen)
  Warum: Eine spezifische Prüfung ist einfacher zu implementieren und zu testen, aber weniger robust gegen zukünftige Angriffe auf andere versteckte Verzeichnisse. Eine generische Lösung erfordert eine klar definierte Liste erlaubter Pfade im Schreibbereich, was die Spec komplexer macht.

F2: Soll die Prüfung nur das Vorhandensein oder den Inhalt von `.git/config` und `.git/hooks/` überwachen, oder auch die Zugriffsrechte (Permissions)?
  Optionen: Inhalt und Existenz | Nur Existenz | Inhalt, Existenz und Rechte
  Warum: Wenn nur die Existenz geprüft wird, könnte ein Angreifer den Inhalt löschen, statt ihn zu ändern, was vielleicht toleriert wird. Wenn Rechte geprüft werden, müssen Tests auch Rechte manipulieren können, was die Testumgebung komplexer macht. Die Anforderung „nicht unbemerkt ändern“ legt inhaltliche Änderungen nahe.

Annahmen:
- keine
