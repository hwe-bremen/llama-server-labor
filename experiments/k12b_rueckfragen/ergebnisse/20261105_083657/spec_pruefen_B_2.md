<!-- spec_pruefen Variante B Wiederholung 2: 6.2 s, prompt 5446, antwort 283, Form: ok -->

F1: Soll `spec-pruefen` auch die Konsistenz der **Vorgabe-Tests** (Dateiinhalt und Pfad) gegen die Spec prüfen, oder nur die technische Struktur der Spec selbst?
  Optionen: Ja, Tests mit prüfen | Nein, nur Spec-Struktur
  Warum: Ändert den Prüfumfang und die zu implementierenden Logik für den Abgleich zwischen Spec-Text und Testdatei.

F2: Wie soll sich `spec-pruefen` verhalten, wenn die Spec **keine** Fehlerpfade oder offenen Fragen enthält?
  Optionen: Als Fehler melden (Strikte Validierung) | Als OK akzeptieren (Minimale Validierung)
  Warum: Bestimmt, ob eine leere oder nicht erfüllte Anforderung an die Spec-Struktur als „Mangel“ gewertet wird.

F3: Sollen bei der Prüfung der Mutanten (R62) auch **Kontrollfluss-Fehler** (wie frühes `return`) automatisch generiert und getestet werden, oder nur die Daten-Integrität?
  Optionen: Ja, inkl. Kontrollfluss | Nein, nur Daten/Integrität
  Warum: Beeinflusst die Komplexität der Testgenerierung und die Tiefe der mechanischen Prüfung.

Annahmen:
- keine
