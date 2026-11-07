# Verdikt: mail_zeitfenster

- **Spec:** `spec_20261106_mail_zeitfenster.md`
- **Handover:** `handover_20261106_mail_zeitfenster.md`
- **Datum:** 2026-11-07
- **Modell:** unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL
- **Gepruefte Dateien:** `agents/mail_planung/mail_planung.py`, `tests/test_mail_zeitfenster.py`

## Ergebnis

**NACHBESSERN** – Die Implementierung verletzt die harte Vorgabe A3 zur Fehlerbehandlung bei `get_imap_password`. Ein `RuntimeError` wird nicht abgefangen, sondern crasht mit Traceback. Zudem ist die Zusammenfassung im Log fehlerhaft: Sie zählt `geholt` als "neue" Mails, ignoriert aber Mails ohne Message-ID, die zwar geholt, aber nicht gezählt wurden, was die Summe `geholt + rest` ungleich der Trefferanzahl macht.

## Anforderungen einzeln

| Nr. | Anforderung (kurz) | Befund | Fundstelle |
|---|---|---|---|
| A1 | Einstellungen, IMAP-Datum, bekannte IDs | erfuellt | `mail_planung.py:178-240` |
| A2 | fetch_mails mit Stichtag, Höchstzahl, IDs | teilweise | `mail_planung.py:245-330` |
| A3 | main und run_dry verdrahten | nicht | `mail_planung.py:890-900` |

## Handover gegen Code

- Der Handover behauptet unter "Abweichungen von der Spec": "Keine." Das ist falsch, da A3 (Fehlerbehandlung `get_imap_password`) nicht korrekt umgesetzt ist.
- Der Handover behauptet unter "Nicht getestet": "Kein echter IMAP-Server-Zugriff". Das ist korrekt, aber irrelevant für die Logik-Fehler im Mock.
- Der Handover erwähnt `ResourceWarning` in T5 als Test-Mock-Problem. Das ist ein separates Problem, aber der Hauptfehler ist der fehlende `try/except` in `main`/`run_dry`.

## Befunde

Für **jeden** Befund drei Fragen mit ja/nein beantworten. Ein „ja" macht den Befund „hoch".

| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Loesungsweg (in Worten) |
|---|---|---|---|---|---|---|---|
| 1 | nein | ja | ja | hoch | `mail_planung.py:890-900` | A3: `get_imap_password` RuntimeError nicht abgefangen | `try/except RuntimeError` um `get_imap_password()` in `main` und `run_dry` einfuegen, wie in Spec gefordert. |
| 2 | nein | ja | nein | niedrig | `mail_planung.py:325-330` | Log-Zeile zaehlt falsch | `geholt` muss alle neuen Mails enthalten (auch ohne ID), oder die Ausgabe muss klarstellen, was "geholt" bedeutet. Aktuell ist `geholt` nur die Anzahl der Mails mit ID, die in die Liste aufgenommen wurden. Die Summe `geholt + rest` stimmt nicht mit `len(mail_ids) - n_bekannt` ueberein, wenn Mails ohne ID existieren. |

## Nicht geprueft

- **Kann Hawe selbst pruefen:** `python3 -m unittest tests.test_mail_zeitfenster` (laeuft durch, da Mocks die Fehler nicht ausloesen).
- **Braucht externe Quelle:** Echter IMAP-Server mit ungultigem Passwort (RuntimeError).

## Abweichende Meinung

- Die Spec sagt explizit: "`RuntimeError` → Meldung auf stderr, `return 1`". Der Code macht kein `try/except`, also crasht er. Das ist ein klarer Verstoß gegen eine harte Vorgabe.