<!-- spec_pruefen Variante B Wiederholung 1: 15.8 s, prompt 5446, antwort 774, Form: ok -->

F1: Welche konkreten Dateien (Pfade) gelten als „Referenzcode“ für die Mutanten-Prüfung?
  Optionen: A) Nur die Quelldatei `kette.py` | B) `kette.py` plus alle Testdateien, die im Repo existieren | C) Nur die Testdateien, die explizit in der Spec genannt sind
  Warum: R51 und R62 verlangen, dass Mutanten (z. B. Entfernen einer Zeile) dazu führen, dass mindestens ein Test rot wird. Ohne die Definition der Referenzdateien ist nicht klar, gegen welchen Code die Mutanten getestet werden.

F2: Wie wird die „mechanische Prüfung ohne Modell“ technisch implementiert?
  Optionen: A) Als eigenständiges Python-Skript, das direkt aufgerufen wird | B) Als neuer Unterbefehl in `kette.py` (z. B. `kette.py spec-pruefen`) | C) Als separater Shell-Wrapper
  Warum: R55 und R61 verweisen auf `kette.py quellen` und `kette.py tests-pruefen`. Die Integration als Subcommand oder Skript bestimmt die Dateistruktur und den Einstiegspunkt für die Tests.

F3: Sollen die Vorgabe-Tests (die die Spec validieren) im gleichen Testlauf wie die Mutanten-Prüfung ausgeführt werden?
  Optionen: A) Ja, in einem einzigen Durchlauf | B) Nein, separat (zuerst Mutanten, dann Tests) | C) Nein, die Spec-Prüfung findet vor der Testerstellung statt
  Warum: R48 und R52 trennen die Erzeugung der Tests (Claude) von der Umsetzung. Die Frage betrifft die Reihenfolge und Isolation der Prüfphasen, was die Spec für den Ablauf von `spec-pruefen` bestimmt.

F4: Was gilt als „Fehlalarm“ im Kontext von `git_schutz` und `alle_tests`?
  Optionen: A) Ein Befund, der im neuen Code nicht existiert, aber im alten Code existierte | B) Ein Befund, der im neuen Code existiert, aber nicht in der Spec gefordert ist | C) Beide oben genannten Fälle
  Warum: R56 warnt vor falschen „hoch“-Befunden des lokalen Reviews. Die Definition von „Fehlalarm“ ist entscheidend, um die Genauigkeit der neuen mechanischen Prüfung gegen die bestehenden Tools (`git_schutz`, `alle_tests`) zu messen.

F5: Wird die Spec-Prüfung auch dann ausgeführt, wenn die Spec keine expliziten Fehlerpfade enthält?
  Optionen: A) Ja, sie prüft immer auf Struktur und Vollständigkeit | B) Nein, sie überspringt den Lauf, wenn keine Fehlerpfade definiert sind | C) Ja, aber nur auf syntaktische Korrektheit
  Warum: R01 verlangt das Durchspielen von Fehlerpfaden. Wenn keine vorhanden sind, muss klar sein, ob die Prüfung trotzdem strukturell läuft oder übersprungen wird, um „Trockenläufe ohne Fehlalarme“ zu gewährleisten.

Annahmen:
- Die Referenz für die Mutanten-Prüfung ist der aktuelle Stand von `kette.py` im Repository.
- Der Befehl wird als Subcommand `spec-pruefen` in `kette.py` implementiert, analog zu `quellen` und `tests-pruefen`.
- „Fehlalarm“ bedeutet, dass der Mechanismus einen Mangel meldet, der in der aktuellen Umsetzung nicht existiert (False Positive).
