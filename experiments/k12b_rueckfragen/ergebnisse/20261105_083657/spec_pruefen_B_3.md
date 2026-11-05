<!-- spec_pruefen Variante B Wiederholung 3: 20.8 s, prompt 5446, antwort 1031, Form: ok -->

F1: Wie soll `spec-pruefen` mit widersprüchlichen oder unvollständigen Anforderungen im Spec-Text umgehen?
  Optionen: A) Fehler melden und Lauf abbrechen (Exit != 0) | B) Warnung ausgeben, aber Mechanik prüfen (Exit 0) | C) Nur prüfen, ob die Mechanik die explizit genannten Fälle abdeckt, andere Lücken ignorieren
  Warum: Bestimmt, ob der Befund als „hoch“ (R16) oder „niedrig“ gewertet wird und ob nachgebessert wird. R21 verbietet Blockaden durch dauerhafte Fehler, aber R20 verlangt Exit != 0 bei Fehlern. Die Frage entscheidet über die Schwelle zwischen „fehlerhafter Spec“ und „unvollständiger Spec“.

F2: Sollen die Vorgabe-Tests, die vor dem Lauf erstellt werden, auch Fehlerpfalte abdecken, die in der Spec nicht explizit als „zu testende Fehler“ genannt sind, aber aus R01/R05 ableitbar sind?
  Optionen: A) Ja, alle aus R01/R05 ableitbaren Fehlerpfade müssen getestet werden | B) Nein, nur die explizit in der Spec unter „Vorgabe-Tests“ oder „Fehlerpfade“ gelisteten Fälle | C) Ja, aber nur solche, die ohne externe Tools (Netz, Disk) prüfbar sind
  Warum: Beeinflusst die Anzahl und den Inhalt der Tests (R48, R51). Wenn A, muss die Spec mehr Fehlerpfade auflisten oder der Testgenerator muss diese inferieren. Wenn B, reicht die Spec als einzige Quelle. R51 verlangt Tests für jeden Fehlerpfad der Tabelle – die Frage ist, was in diese Tabelle kommt.

F3: Wie soll mit Anforderungen umgegangen werden, die technisch unmöglich oder widersprüchlich zu anderen Anforderungen sind (z. B. „immer lokal speichern“ vs. „Netzwerk-Timeout 1s“)?
  Optionen: A) Spec als fehlerhaft markieren, Lauf abbrechen | B) Die unmögliche Anforderung ignorieren und den Rest prüfen | C) Eine plausible Standardannahme treffen und diese als Annahme dokumentieren
  Warum: R02 verbietet Erfinden von Fakten, aber R05 warnt vor Prüfungen, die Normalbetrieb verbieten. Wenn die Spec selbst widersprüchlich ist, ist das ein Spec-Fehler. Die Frage entscheidet, ob der Mechanismus die Spec ablehnt (R15) oder eine Interpretation vornimmt (R02-Verstoß, wenn nicht dokumentiert).

F4: Soll `spec-pruefen` auch prüfen, ob die Spec-Datei selbst konsistent formatiert ist (z. B. korrekte Markdown-Struktur, keine leeren Pflichtabschnitte), oder nur den inhaltlichen Teil?
  Optionen: A) Ja, volle syntaktische Konsistenz der Spec-Datei prüfen | B) Nein, nur inhaltliche Elemente (Anforderungen, Fehlerpfade, Tests) prüfen | C) Ja, aber nur kritische Strukturmerkmale (z. B. Existenz von „## Fehlerpfade“)
  Warum: Beeinflusst den Umfang der mechanischen Prüfung. R56 warnt vor falschen Befunden durch lokale Reviews. Wenn die Formatierung Teil der „Mechanik“ ist, muss das geprüft werden. Wenn nicht, fällt das weg.

F5: Wie soll die Gegenprobe (R10) durchgeführt werden: Durch Ausführen der Tests gegen den alten Code oder durch statische Analyse, ob die Tests den alten Code abdecken?
  Optionen: A) Ausführen der Tests gegen den alten Code (wenn vorhanden) | B) Statische Analyse: Prüfen, ob die Testfälle mit dem alten Code rot werden würden (Mutation) | C) Keine Gegenprobe in `spec-pruefen`, nur im separaten Schritt
  Warum: R10 verlangt „Rot vorab“. Wenn der alte Code nicht verfügbar ist (z. B. bei neuer Spec), muss die Gegenprobe simuliert werden. R51 erwähnt Mutation. Die Frage bestimmt, ob `spec-pruefen` selbst Tests ausführt oder nur auf deren Existenz und Struktur prüft.

Annahmen:
- Die Spec-Datei ist im Repo vorhanden und wird vor dem Lauf committed (R61).
- Es gibt keine externen Abhängigkeiten für die mechanische Prüfung der Spec selbst (nur Python-Standardbibliothek).
- „Fehlerpfade“ in der Spec sind klar abgegrenzte Sektionen, die von den Anforderungen getrennt sind.
- Keine Rückfragen zu technischen Details der Implementierung von `spec-pruefen` (z. B. welche Bibliotheken verwendet werden), da dies Teil der Umsetzung ist.
