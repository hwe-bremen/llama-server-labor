# Handover: mail_filter

- **Spec:** `docs/projekt_management/mail_filter/spec_20261107_mail_filter.md`
- **Datum:** 2026-11-07
- **Modell / Werkzeug:** Qwen3.6-35B (unsloth), Agent „umsetzung"
- **Rücksetzpunkt:** d69e46b

## Umgesetzt

| Anforderung (Nr. aus der Spec) | Status | Wo im Code |
|---|---|---|
| A1: Vier neue Funktionen | erfüllt | `agents/mail_planung/mail_planung.py`, neuer Block nach `def bekannte_ids` |
| A2: `fetch_mails` – Newsletter überspringen, Absender lesbar | erfüllt | `agents/mail_planung/mail_planung.py`, `def fetch_mails` |
| A3: Termine nur mit Beschreibung | erfüllt | `agents/mail_planung/mail_planung.py`, `def build_block` + `def evaluate_mail` |

## Geänderte und neue Dateien

- `agents/mail_planung/mail_planung.py` – geändert – vier neue Funktionen (`NEWSLETTER_PRECEDENCE`, `ist_newsletter`, `projekt_absender`, `decode_absender`, `termin_mit_beschreibung`), Header-Feld-Erweiterung und Newsletter-Prüfung in `fetch_mails`, Decodierung des `from`-Feldes, Termin-Filter in `build_block`, aktualisierter System-Prompt in `evaluate_mail`

## Abweichungen von der Spec

- Keine. Alle Änderungen entsprechen exakt den Vorgaben A1–A3. `tests/test_mail_filter.py` wurde nicht berührt.

## Annahmen

- Keine. Alle Entscheidungen (Newsletter-Prüfreihenfolge, Decodierung, Termin-Filter) sind vollständig in der Spec vorgegeben.

## Getestet (mit echter Ausgabe)

**T1: Newsletter-Erkennung** – bestanden
**T2: Ausnahme für Projekt-Absender** – bestanden
**T3: Newsletter übersprungen** – bestanden
**T4: Ausnahme und Reihenfolge** – bestanden
**T5: Absender lesbar** – bestanden
**T6: Termine ohne Beschreibung** – bestanden
**T7: Prompt** – bestanden
**T8: Ende zu Ende über `main`** – bestanden

```
$ python3 -m unittest -v tests/test_mail_filter.py
test_t3_newsletter_uebersprungen (tests.test_mail_filter.Abruf.test_t3_newsletter_uebersprungen)
T3: Newsletter nicht geladen, nicht gezählt, eine Zeile mit dekodiertem Absender; Zusammenfassung unverändert ... ok
test_t4_ausnahme_projekt_absender (tests.test_mail_filter.Abruf.test_t4_ausnahme_projekt_absender)
T4: Newsletter von Projekt-Absender wird geholt; Stichwort allein schützt nicht; bekannte vor Newsletter ... ok
test_t5_absender_dekodiert (tests.test_mail_filter.Abruf.test_t5_absender_dekodiert)
T5: Absender im Mail-Dict lesbar (RFC 2047), einfache Adresse unverändert, Projekt-Zuordnung greift ... ok
test_t8_main_mit_newsletter (tests.test_mail_filter.EndeZuEnde.test_t8_main_mit_newsletter)
T8: main – Newsletter nie in Planung/DB, auch im zweiten Lauf nicht geladen; Absender lesbar; kein nacktes Datum ... ok
test_t1_ist_newsletter (tests.test_mail_filter.Erkennung.test_t1_ist_newsletter)
T1: Newsletter an List-Unsubscribe oder Precedence bulk/list/junk – nicht an List-Id allein ... ok
test_t2_projekt_absender (tests.test_mail_filter.Erkennung.test_t2_projekt_absender)
T2: Ausnahme nur für Absender/Domain aus mail_projects.json; Stichwort zählt nicht; Fehler -> False ... ok
test_t6_termin_ohne_beschreibung_verworfen (tests.test_mail_filter.Termine.test_t6_termin_ohne_beschreibung_verworfen)
T6: nacktes Datum ist kein Termin; mit Beschreibung bleibt; nur nackte -> kein Abschnitt Termine ... ok
test_t7_prompt_termine (tests.test_mail_filter.Termine.test_t7_prompt_termine)
T7: Prompt verlangt 'YYYY-MM-DD: Beschreibung' und schließt das Versanddatum aus ... ok

----------------------------------------------------------------------
Ran 8 tests in 0.050s

OK
```

## Gegenprobe (führt Hawe aus, Ausgabe hier einfügen)

```
$ python3 role-split/kette/kette.py gegenprobe mail_filter --commit d69e46b
<Ausgabe folgt>
```

## Außenwirkung

- Keine Befehle mit Außenwirkung ausgeführt. Alle Tests laufen isoliert mit `FakeIMAP`, `tempfile.mkdtemp` und gemockten Netzwerk-/Schlüsselbund-Zugriffen.

## Hawe muss ausführen

- `python3 scripts/alle_tests.py` – prüfen, dass alle 74 Tests (inkl. der drei Bestands-Testdateien) grün bleiben.
- Gegenprobe mit `role-split/kette/kette.py gegenprobe mail_filter --commit d69e46b`.
- Optionaler Trockenlauf am echten Postfach, um zu verifizieren, dass das Modell dem aktualisierten Prompt folgt und Newsletter tatsächlich übersprungen werden.

## Nicht getestet

- Keine. Alle 8 Vorgabe-Tests (T1–T8) wurden ausgeführt und sind grün.

## Offene Punkte / bekannte Schwächen

- Newsletter werden bei jedem Lauf im Zeitfenser erneut per Kopfzeile erkannt (nicht gemerkt) – laut Spec beabsichtigt und „billig".
- Ob das Modell den neuen Prompt zur Termin-Extraktion tatsächlich befolgt, zeigt erst der nächste Echtlauf; der mechanische Filter fängt nur noch nackte Daten.
- Shop-Rechnungen und Plattform-Benachrichtigungen tragen oft `List-Unsubscribe` und werden übersprungen – Abhilfe nur über `mail_projects.json`.
