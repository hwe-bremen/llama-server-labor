# Kette 7 mail_server_test (23./24.10.2026)
Aufgabe: mail_planung erstmals gegen einen echten Testserver (GreenMail in Docker) und das echte Modell, mit 16 synthetischen Mails.
Ergebnis: nicht bestanden (Schwelle) – aber Werkzeug läuft echt durch, E2E grün. Danach Entscheidung **Hybrid**.

## Was durchrutschte (oder fast)
| Defekt | Fehlerklasse | Gefunden durch |
|---|---|---|
| Spec A5: „Nicht-localhost → Exit 1" hätte Echtbetrieb blockiert; Port 3143 ist unverschlüsselt | Spec-Fehler nach 4 Runden | Claude |
| Testläufe ohne Test-Schlüsselbund-Dienst/Port/User → **echter Dienst** gelesen | stille Außenwirkung | Claude (beide Review-Läufe verfehlt) |
| Aufräumen nur `trap ERR` | Absicherung läuft ins Leere | Claude (Review verfehlt, behauptete Gegenteil) |
| Prüfskript prüfte das Postfach statt der Planungsdatei | verlangt, aber nicht abgesichert | teils Review Lauf 2 |
| `starttls()` auf unverschlüsseltem SMTP | Umgebung | **Review Lauf 2** (Claude übersah) |
| Blankes `except:` fing `SystemExit`; Docker-Port vor Dienst; Umlaute in `smtplib`; Mails ins falsche Postfach | Umgebung/Technik | echter Lauf |
| **`unknown-8bit` im Betreff → eine Mail stoppte den ganzen Lauf** (Fehler im K6-Werkzeug) | eine Eingabe blockiert alles | echter Lauf |
| Testdaten passten nicht zu Erwartungen und Spec | Testdaten-Konsistenz | echter Lauf (niemand vorher) |
| NB3: Umsetzer ersetzte Testdatei außerhalb des Auftrags, behauptete „mail_planung.py existiert nicht" | Arbeit außerhalb des Auftrags | Claude |

## Regeln daraus
- R05, R06, R13, R14 (echter Lauf Pflicht), R19 (noch nicht im Prompt), R20, R21, R23–R26, R29, R32, R33
- Umgesetzt: `MAIL_IMAP_UNENCRYPTED` + localhost, `MAIL_IMAP_KEYCHAIN_SERVICE`, `_safe_decode`/`decode_subject` (Tests K16), Startskript mit `trap EXIT`, Protokoll-Gruß-Prüfung, frisches `mktemp`

## Sonst bemerkenswert
- Mit echtem Modell bestätigt: Injection-Mail ignoriert, Kürzung, Dedup, Duplikat-Hinweis, Projektzuordnung, Umlaute, zweiter Lauf byte-identisch.
- Claude hat im E2E 8 kleine Korrekturen selbst gemacht (Abweichung von „Korrekturen macht OpenCode", bewusst wegen Tempo).
- Qwen3.6-35B-A3B als Umsetzer: spec-treu (auch bei fehlerhafter Spec), schnell; ungenaue Übergabe (Dateinamen, Image-Version).
