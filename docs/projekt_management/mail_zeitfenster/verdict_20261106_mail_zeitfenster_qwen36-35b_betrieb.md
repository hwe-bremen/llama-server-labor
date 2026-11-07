# Verdikt: Betriebssicherheit und Spec-Alignment

- **Spec:** `spec_20261106_mail_zeitfenster.md`
- **Handover:** `handover_20261106_mail_zeitfenster.md`
- **Datum:** 2026-11-07
- **Modell:** unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL
- **Gepruefte Dateien:** `agents/mail_planung/mail_planung.py`, `tests/test_mail_zeitfenster.py`

## Ergebnis

**PASS** – Die Umsetzung der Spec ist vollständig und korrekt. Die Trennung von Header-Check und Body-Download funktioniert wie spezifiziert. Es gibt keine Datenverlust-Risiken und keine Verstöße gegen harte Vorgaben.

## Anforderungen einzeln

| Nr. | Anforderung (kurz) | Befund | Fundstelle |
|---|---|---|---|
| A1 | Einstellungen, IMAP-Datum, bekannte IDs | erfuellt | `mail_planung.py:176-239` |
| A2 | fetch_mails mit Stichtag, Höchstzahl, bekannten IDs | erfuellt | `mail_planung.py:242-328` |
| A3 | main und run_dry verdrahten | erfuellt | `mail_planung.py:840-935` |
| T1-T8 | Tests | erfuellt | `test_mail_zeitfenster.py` |

## Handover gegen Code

- Der Handover behauptet „Keine Abweichung von der Spec". Dies wird durch den Code bestätigt.
- Der Handover erwähnt `ResourceWarning: unclosed database` in T5 als Test-Mock-Problem. Im Code ist dies nicht sichtbar, aber im Test-Kontext plausibel und irrelevant für den Produktbetrieb.
- Die Implementierung von `zeitfenster()` liest die Werte beim Aufruf (nicht Import), wie gefordert.
- Die Logik für `max_anzahl` zählt nur Mails *mit* Message-ID in die Begrenzung, holt aber Mails ohne ID immer. Dies entspricht der Spec und den Tests.

## Befunde

| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Loesungsweg (in Worten) |
|---|---|---|---|---|---|---|---|
| 1 | nein | nein | nein | niedrig | `mail_planung.py:275` | **Geringe Redundanz:** `import email` ist lazy importiert, wird aber auch in der Schleife verwendet. Da `email` ein Standardmodul ist, ist der Overhead minimal. | Nicht notwendig. |
| 2 | nein | nein | nein | niedrig | `mail_planung.py:315` | **Logik-Check:** `rest` wird inkrementiert, wenn `max_anzahl` erreicht ist. Die Ausgabe zeigt `rest` als „beim nächsten Lauf". Das ist korrekt. | Nicht notwendig. |

## Nicht geprueft

- **Kann Hawe selbst pruefen:** Echter IMAP-Zugriff mit großem Postfach (>100 Mails), um Performance und Pufferung zu testen.
- **Braucht externe Quelle:** Keine.

## Abweichende Meinung

Keine. Die Implementierung ist sauber und hält sich strikt an die Vorgaben. Der Fokus auf `BODY.PEEK[HEADER.FIELDS (MESSAGE-ID)]` ist effizient und korrekt.