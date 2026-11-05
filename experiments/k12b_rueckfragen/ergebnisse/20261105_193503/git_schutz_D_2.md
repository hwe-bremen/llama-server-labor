<!-- git_schutz Variante D Wiederholung 2: 14.7 s, prompt 8421, antwort 394, Form: ok -->

F1: Soll die Schutzmaßnahme auch das Verbot von Schreibzugriffen auf `.git/hooks/` umfassen, oder beschränkt sie sich strikt auf `.git/config`?
  Optionen: Nur `.git/config` | `.git/config` und `.git/hooks/`
  Warum: Dies bestimmt den exakten Umfang der „technischen Sperre“ in der Spec und die entsprechenden Tests (Mutationen, die Hooks manipulieren). Die Aufgabe nennt explizit `.git/config` als Anlass, erwähnt `.git/hooks/` aber nur implizit durch „nicht unbemerkt ändern können“ im Kontext der Sicherheitslücke.

F2: Darf der Umsetzer den Schutzmechanismus in eine neue Datei auslagern (z. B. `role-split/kette/git_schutz.py`), oder muss er ihn in bestehende Dateien der Kette integrieren?
  Optionen: Neue Datei erlauben | Nur bestehende Dateien (`kette.py` etc.)
  Warum: Dies beeinflusst den „Schreibbereich“ in der Spec und die Komplexität der Umsetzung. Eine neue Datei ist sauberer, aber die Regel R07 („Nur die im Auftrag genannten Dateien ändern“) könnte als Einschränkung ausgelegt werden, wenn keine neue Datei explizit erlaubt ist.

F3: Sollen Tests für den Fall vorgesehen werden, dass `.git/config` existiert, aber nicht lesbar ist (z. B. Berechtigungsfehler), oder wird dies als nicht relevant ausgeschlossen?
  Optionen: Testfall für „nicht lesbar“ einfügen | Nicht relevant (Auslassen)
  Warum: Dies bestimmt die Abdeckung der Fehlerpfade in der Spec. Ein nicht lesbarer Config-File ist ein realistischer Betriebszustand, der das Tool sonst crashen lassen könnte (R24/R20).

Annahmen:
- keine
