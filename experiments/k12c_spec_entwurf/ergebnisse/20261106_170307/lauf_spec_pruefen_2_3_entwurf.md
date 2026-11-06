# Spec: lauf_spec_pruefen

- **Datum:** 2026-11-06
- **Modell:** lokales Modell (Messung K12c)
- **Betroffene Dateien:** `role-split/kette/kette.py`, `role-split/kette/spec_pruefen.py`
- **Änderungsstellen:** 3

## Ziel

`kette.py spec-pruefen` soll statt der groben Größenzählung (`groesse`) die detaillierten Befunde der mechanischen Spec-Prüfung (`spec_pruefen.py`) ausgeben und verwerten. Die Größe der Spec wird zum reinen Hinweis degradiert, der nicht mehr zum Urteil „NACHBESSERN" führt.

## Nicht-Ziele

- Änderung der Logik in `spec_pruefen.py` selbst (die prüft weiterhin strukturell).
- Änderung der `urteil`-Logik in `kette.py` (die wertet weiterhin nur „hoch" und „offen" aus).
- Änderung der Prompt-Vorlagen für den Umsetzer.

## Schreibbereich

- `role-split/kette/kette.py`
- `role-split/kette/spec_pruefen.py`
- `tests/test_lauf_spec_pruefen.py`

## Vorgabe-Tests

- `tests/test_lauf_spec_pruefen.py`

## Außenwirkung und Sperre

- **Was kann die Aufgabe außerhalb des Repos auslösen?** nichts
- **Technische Sperre für Tests:** keine (reine Logik-Änderung, Datei-I/O).

## Einstiegspunkte

| Datei | Wie gestartet | Test |
|---|---|---|
| `role-split/kette/kette.py` | `python3 role-split/kette/kette.py spec-pruefen <kurztitel>` | T1 |
| `role-split/kette/spec_pruefen.py` | Import als Modul | T2 |

## Quellen

- `role-split/kette/kette.py` `def spec_pruefen` – aktueller Aufruf von `groesse` und Ausgabe
- `role-split/kette/spec_pruefen.py` `def pruefe` – Rückgabe von `befunde` und `hinweise`
- `role-split/kette/spec_pruefen.py` `def _groesse` – interne Größenermittlung (wird nur noch als Hinweis genutzt)
- `role-split/kette/kette.py` `def urteil` – Definition, was „hoch" und „offen" bedeutet (zur Verifikation, dass Größe nicht betroffen ist)

## Anforderungen

### A1: Mechanische Prüfung statt Größenzählung
- **Anforderung:** `kette.py spec-pruefen` ruft `spec_pruefen.pruefe` auf, gibt die zurückgegebenen `befunde` und `hinweise` strukturiert aus und beendet sich mit Exit 0, wenn keine `befunde` vorliegen.
- **Stelle:** `role-split/kette/kette.py` `def spec_pruefen`
- **Akzeptanz:** Ausgabe enthält die Zeilen der Befunde; Exit-Code 0 bei sauberer Spec.

### A2: Größe als Hinweis
- **Anforderung:** Die Größenermittlung (`spec_pruefen._groesse`) wird weiterhin durchgeführt, das Ergebnis wird aber nur unter „Hinweise" ausgegeben und führt nicht mehr zu einem Fehler oder einer Blockade.
- **Stelle:** `role-split/kette/kette.py` `def spec_pruefen`
- **Akzeptanz:** Auch bei sehr großer Spec (über 1000 Zeilen) ist der Exit-Code 0, sofern keine anderen Befunde vorliegen.

### A3: Fehler bei fehlender Spec-Prüfung
- **Anforderung:** Wenn `spec_pruefen.pruefe` eine Ausnahme wirft oder nicht gefunden wird, gibt `kette.py spec-pruefen` eine Fehlermeldung aus und endet mit Exit 2.
- **Stelle:** `role-split/kette/kette.py` `def spec_pruefen`
- **Akzeptanz:** Exit-Code 2 bei Implementierungsfehlern.

### A4: Konsistente Ausgabe
- **Anforderung:** Die Ausgabe von `spec-pruefen` beginnt mit der Zeile `## Befunde` gefolgt von einer Liste der Befunde (falls vorhanden), dann `## Hinweise` gefolgt von der Liste der Hinweise (falls vorhanden). Wenn beide leer sind, wird „Keine Befunde / Keine Hinweise" ausgegeben.
- **Stelle:** `role-split/kette/kette.py` `def spec_pruefen`
- **Akzeptanz:** Ausgabeformat ist konsistent und maschinenlesbar.

## Fehlerpfade

| Anforderung | Fall | Was ist vorher schon geschrieben/markiert? | Erwartetes Verhalten (Exit-Code, Datei, Meldung) | Test |
|---|---|---|---|---|
| A1 | Spec existiert nicht | Datei `docs/projekt_management/anforderung_...` oder Spec nicht gefunden | Exit 2, Meldung „Spec nicht gefunden" | T3 |
| A1 | Spec ist leer | Spec-Datei existiert, aber Text ist leer | Exit 0, Ausgabe „Keine Befunde / Keine Hinweise" | T4 |
| A2 | Spec ist extrem groß | Spec > 1000 Zeilen | Exit 0, Hinweis zur Größe, keine Befunde | T5 |
| A3 | Spec-Prüfung fehlschlägt | `spec_pruefen.pruefe` wirft Exception | Exit 2, Fehlermeldung | T6 |
| A4 | Keine Befunde, keine Hinweise | Saubere Spec | Exit 0, Ausgabe „Keine Befunde / Keine Hinweise" | T7 |
| A4 | Nur Befunde, keine Hinweise | Spec mit Fehlern, aber keine Hinweise | Exit 0, Ausgabe nur Befunde | T8 |

## Testplan

Alle Tests werden als `tests/test_lauf_spec_pruefen.py` (unittest) umgesetzt, je Test eine Methode `test_<id>_…`. Kein Test hat Außenwirkung.

### T1: Spec-Prüfung läuft erfolgreich
- **Prüft:** A1, A4
- **Aufbau:** Temporäre Spec-Datei mit allen Pflichtabschnitten, aber ohne Fehler.
- **Erwartung:** Exit-Code 0, Ausgabe enthält „Keine Befunde / Keine Hinweise".
- **Warum misst der Test das Richtige?** Der Test simuliert den Normalfall einer sauberen Spec.
- **Gegenprobe:** Keine (neuer Test).

### T2: Spezifikation wird korrekt importiert
- **Prüft:** A1
- **Aufbau:** Import von `spec_pruefen` und Aufruf von `pruefe` mit einer gültigen Spec.
- **Erwartung:** Funktion gibt `(befunde, hinweise, groesse)` zurück, wobei `befunde` leer ist.
- **Warum misst der Test das Richtige?** Prüft, dass die Schnittstelle korrekt funktioniert.
- **Gegenprobe:** Keine (neuer Test).

### T3: Fehlende Spec wird erkannt
- **Prüft:** A3
- **Aufbau:** Aufruf von `spec-pruefen` mit einem nicht existierenden Kurztitel.
- **Erwartung:** Exit-Code 2, Fehlermeldung „Spec nicht gefunden".
- **Warum misst der Test das Richtige?** Prüft die Fehlerbehandlung für fehlende Dateien.
- **Gegenprobe:** Keine (neuer Test).

### T4: Leere Spec wird akzeptiert
- **Prüft:** A1, A4
- **Aufbau:** Temporäre Spec-Datei mit Inhalt nur aus Leerzeichen.
- **Erwartung:** Exit-Code 0, Ausgabe „Keine Befunde / Keine Hinweise".
- **Warum misst der Test das Richtige?** Prüft, dass leere Specs nicht als Fehler gewertet werden.
- **Gegenprobe:** Keine (neuer Test).

### T5: Große Spec wird nur als Hinweis gewertet
- **Prüft:** A2
- **Aufbau:** Temporäre Spec-Datei mit > 1000 Zeilen, aber ohne Fehler.
- **Erwartung:** Exit-Code 0, Ausgabe enthält Hinweis zur Größe.
- **Warum misst der Test das Richtige?** Prüft, dass die Größe nicht zum Fehler führt.
- **Gegenprobe:** Keine (neuer Test).

### T6: Fehler in Spec-Prüfung wird abgefangen
- **Prüft:** A3
- **Aufbau:** Mock von `spec_pruefen.pruefe`, der eine Exception wirft.
- **Erwartung:** Exit-Code 2, Fehlermeldung.
- **Warum misst der Test das Richtige?** Prüft die Fehlerbehandlung für Implementierungsfehler.
- **Gegenprobe:** Keine (neuer Test).

### T7: Nur Befunde, keine Hinweise
- **Prüft:** A4
- **Aufbau:** Spec mit einem Fehler (z. B. fehlender Abschnitt), aber keine Hinweise.
- **Erwartung:** Exit-Code 0, Ausgabe nur Befunde.
- **Warum misst der Test das Richtige?** Prüft die korrekte Ausgabe bei Fehlern.
- **Gegenprobe:** Keine (neuer Test).

### T8: Nur Hinweise, keine Befunde
- **Prüft:** A4
- **Aufbau:** Spec mit einer Größe über dem Schwellenwert, aber keine Fehler.
- **Erwartung:** Exit-Code 0, Ausgabe nur Hinweise.
- **Warum misst der Test das Richtige?** Prüft die korrekte Ausgabe bei Hinweisen.
- **Gegenprobe:** Keine (neuer Test).

## Offene Fragen

- Keine

## Abweichende Meinung

- Keine
