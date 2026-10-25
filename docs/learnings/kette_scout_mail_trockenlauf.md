# Kette R1/R2 scout_mail_trockenlauf + scout_mail_nachbesserung (17.10.2026)
Aufgabe: Scout-Mail mit Trockenlauf (Datei statt Versand) und Fehler-Mail statt Schweigen; Runde 2 Nachbesserung.
Ergebnis: nicht bestanden – der wichtigste Defekt (Hänger) wurde in vier Modellschritten nie als „hoch" erkannt.

## Was durchrutschte (oder fast)
| Defekt | Fehlerklasse | Gefunden durch |
|---|---|---|
| `smtplib.SMTP` ohne Timeout → Fehler-Mail hängt im Störungsfall unbegrenzt | Netz ohne Timeout | Claude (Test mit schweigendem Socket) |
| `--dry-run --fail-mail` → echter SMTP-Versuch | Schalter-Kombination nicht durchgespielt | Claude |
| Runde 2: Agent startete Pipeline ohne Trockenlauf → **echter Gmail-Versand** | Außenwirkung ohne technische Sperre | Agent selbst genannt, Review „niedrig" |
| Übergabe: „Abweichungen: Keine", „automatische Bereinigung" – beides falsch | falsche Behauptungen in Übergabe | Claude |
| Review gewichtete Befunde durchweg zu niedrig; Urteil öfter richtig als Begründung | Schwere-Einschätzung | Claude |

## Regeln daraus
- R04 technische Sperre (umgesetzt: `SCOUT_ALLOW_SEND`, Prüfung vor `get_password()`)
- R08 Übergabe prüfen · R16 Schwere mechanisch (`kette.py urteil`) · R17 zwei Läufe vereinigen · R27 Timeout

## Sonst bemerkenswert
- Spec (Qwen3.8) sehr gut (~7/8), aber erfundene Zeilennummern → später Abschnitt „Quellen" (R02).
- Doppel-Review + Merge zuerst hier als Idee („keiner der beiden Läufe allein richtig").
