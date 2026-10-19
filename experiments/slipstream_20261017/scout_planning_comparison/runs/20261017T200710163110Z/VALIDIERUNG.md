# Scout-Planungsdiskussion: Slipstream-Ergebnis

## Ergebnis

**Technisch vollständig, fachlich nur teilweise brauchbar.** Der Originalauftrag wurde mit den vier vollständigen Dateien und aktueller Review-Rolle beantwortet. Die Antwort endet regulär nach1072Tokens/454Wörtern, bleibt bei einer Diskussion und stellt genau eine Rückfrage. Keine Spec und keine Umsetzung ausgeführt.

Das Modell erkennt den Kalenderjahr-/ISO-Jahr-Mismatch und zeigt einen tatsächlich fehlerhaften Dateinamensfall. Sein vorgeschlagener Schutz **pro Tag** erfüllt aber die Anforderung **kein zweiter Versand in derselben Woche** nicht. Deshalb diese Antwort nicht unverändert als Grundlage einer Implementierung übernehmen.

Originalantwort unverändert: answer.txt, SHA-256 `8d186589a9f9ea660fbdbc61e44c815fc1df73e71d36884f204380a1945a9389`.

## Aussagen gegen den fixierten Code geprüft

| Aussage | Bewertung |
|---|---|
| Writer verwendet Kalenderjahr, Mailer ISO-Jahr | Richtig, nach anfänglicher unklarer Formulierung selbst korrigiert. |
| 01.01.2027: Writer kw53_2027, Mailer sucht kw53_2026 | Richtig; konkreter Nachweis des Mismatch. |
| 29.12.2026 sei KW52 | Falsch: ISO2026-W53. |
| 01.01.2027 sei Donnerstag | Falsch: Freitag; ISO2026-W53 trotzdem korrekt bestimmt. |
| Es fehlt Prüfung auf bereits erfolgten Versand | Richtig. Zweimaliger mode_normal-Aufruf ruft den SMTP-Stub zweimal auf. |
| Zweiter Pipeline-Lauf überschreibe den Bericht | Zu pauschal: Ohne neue Items beendet sich Scout vor dem Schreiben. Trotzdem kann der Wrapper erneut den alten Bericht versenden. |
| Schutz gegen erneuten Versand pro Tag | Falsche Anforderungseinheit: Montag und Dienstag derselben ISO-KW bleiben zwei mögliche Sendetage. |

Der Tagesfehler betrifft den Lösungsvorschlag, nicht nur eine beiläufige Formulierung: Die Antwort fordert ausdrücklich eine „Versand-Sperre pro Tag“ mit Prüfung, ob „heute“ schon versendet wurde. Gegenbeispiel19.10./20.10.2026: verschiedene Tage, beide ISO2026-W43. Für den Nutzerauftrag müsste die Identität mindestens aus ISO-Jahr und ISO-KW bestehen; daraus folgt noch keine automatische Nachsendepolitik.

Die Einleitung vermischt außerdem die Ursachen: Falsche Wochen-/Jahreszuordnung und fehlender Versandzustand sind unabhängige Probleme. Auch nach Korrektur des Dateinamens kann die vorhandene Datei ohne Versandhistorie erneut verschickt werden.

Die beschriebene SCOUT_ALLOW_SEND-Sperre ist grundsätzlich korrekt als Außenwirkungssperre erkannt. Sie ersetzt keinen Deduplizierungszustand im freigegebenen realen Versandbetrieb. Die Antwort liefert keine ausgearbeitete Lösung für parallele Läufe oder den Zwischenzustand SMTP angenommen, Versandmarkierung noch nicht gespeichert; das war hier eine erste Diskussion, keine angeforderte vollständige Spec.

## Rückfrage und Planung

Die eine Rückfrage „ISO-Jahr oder Kalenderjahr?“ ist verständlich und empfiehlt ISO-Jahr. Sie ist aber weniger entscheidend als das Modell darstellt: Ein durchgängiger ISO-Jahr/KW-Schlüssel passt zur bereits verwendeten ISO-KW. Nur überall Kalenderjahr zu verwenden, während die KW ISO-basiert bleibt, kann eigene Zuordnungsprobleme erzeugen. Die fehlende Angabe eines konkreten Lösungswegs macht den Arbeitsauftrag nicht allein unbrauchbar; einen solchen Weg zu entwickeln war gerade die Planungsaufgabe.

Die Antwort wahrt die Diskussionsphase und führt keine Außenwirkungen aus. Sie ist kürzer und weniger repetitiv als der vorige Slipstream-Diffreview. Ein qualitativ verlässlicher Wochenversand-Entwurf ist damit noch nicht belegt.

## Vergleich zur geposteten Qwen3.8-Antwort

Beide Antworten erkannten fehlenden Versandzustand und den Jahres-Mismatch, behaupteten zu pauschal das Überschreiben bei jedem zweiten Lauf und enthielten falsche Kalenderangaben.

- **Qwen3.8:** brauchbarer Ansatz mit persistentem Versandzustand nach Jahr/KW; erweitert den Auftrag ohne Grundlage um Nachsenden älterer Wochen. Die allgemeine Kalendererklärung war falsch, Trigger nicht konkret nachgerechnet.
- **Slipstream Qwen3.6-35B:** konkreter zutreffender Dateinamens-Mismatch am01.01.2027, aber fehlerhafte Tages-Deduplizierung. Keine vergleichbare umfassende Nachsende-Erweiterung.

**Kein klarer Qualitätsgewinn durch das getestete Streaming-Modell.** Beide Antworten benötigen Prüfung und fachliche Eingrenzung; die falsche Tagesgrenze ist eine praktisch relevante Fehlplanung. Kein Gesamtscore oder Modellranking aus einem einzelnen Planungsfall.

Die Auswertung ist nicht blind: Qwen3.8s Antwort und eigene Korrekturen waren dem auswertenden Assistenten bekannt. Sie wurden nicht an Slipstream übertragen. Originalprompt, Snapshots und Nachrichten sind weiterhin hashidentisch. Qwen3.8 hatte UI-/ggf.Tool-Kontext; Slipstream bekam alle vier Dateien inline. Exakte UI-Prompts, Samplingwerte und Tooltranskripte liegen nicht vor. Für den Scout-UI-Lauf gibt es keine aufgezeichnete Laufzeit; die früher gemessenen218,90s gehörten zu einem anderen Diffreview und werden hier nicht als direkter Zeitvergleich verwendet.

## Messwerte

| Größe | Slipstream-Diskussionslauf |
|---|---:|
| Laden bis health | 144,74s |
| Prompttokens | 13.772 |
| Ausgabetokens | 1.072 |
| Erster sichtbarer Text | 1122,52s, etwa18min43s |
| Anfrage gesamt | 1370,72s, etwa22min51s |
| Native Prompt-Tokens/s | 12,27 |
| Native Decode-Tokens/s | 4,32 |
| Peak beobachtetes Prozess-RSS | 7,10GiB |
| Zusätzliche Swapouts | 0 |
| Finish / Vollständigkeit | stop / vollständig |

Der größte Zeitanteil liegt vor dem ersten Antworttext in der Eingabeverarbeitung; nur rund4min08s native Decode. Modellladen plus Anfrage etwa25min15s. Kein Ausgabelimitproblem in diesem Lauf. Kontext32768, Cache2GiB, Reserve8GiB, Batch32,IO1,MTP4, Temp0/Seed42, Thinkingoff, Ausgaberahmen4096. GGUF extern/PGRN intern.

Separater Denktext leer; separate Reasoning-Tokenzahl nicht berichtet. Kein Nachweis messbar ausgeschalteter interner Denkprozesse. Positive native Cache-Misses1703126. RSS nicht mit gesamter Unified-Memory-Belegung gleichsetzen. Alle aufgezeichneten Swapout-Werte13528351; bereits belegter Swap vor/nachher4894,38MiB.

## Nachprüfungen und Abschluss

verify_claims.py/claim-checks.json dokumentieren die nach Kenntnis der Antwort vorgenommenen Prüfungen. Pythons Datumsfunktionen berechnen die behaupteten Tage/Wochen. Ausschließlich die vertrauenswürdige Funktion mode_normal aus dem fixierten Repo wird mit In-Memory-Stubs für Reportsuche, MIME-Bau und SMTP geprüft; zweimal Exit0 und zwei Stub-Sendeaufrufe. Kein vollständiger Pipeline-Import/-Start, keine echten Dateien/DBs verändert, kein Netzwerk, Schlüsselbund oder SMTP verwendet. Modelltext niemals ausgeführt.

EngineExit0, kein Safety-Abbruch/Zwangscleanup,8083frei, Labor blieb gestoppt, Arbeitsdateien/Index/HEAD unverändert. Kein erneuter Modelllauf. Originallogs bleiben unverändert erhalten.

**Empfehlung:** Das Streaming-Experiment ist technisch bestätigt. Für das Ziel eines praktisch stärkeren Codeprüfers diese Konfiguration vorerst nicht weiter ausbauen: lange Eingabeverarbeitung ohne belegten Qualitätsgewinn. Die fachliche Spec lieber mit dem vorhandenen Qwen3.8 und expliziter ISO-Jahr/KW-Identität weiterentwickeln, mit menschlicher Gegenprüfung der Kalenderfälle, Wiederholungen und Versand-Zwischenzustände. Das wäre anschließend Entwicklungsarbeit mit Korrekturhinweisen, kein unabhängiger Blindtest. Eine Spec oder Umsetzung wurde hier nicht automatisch erstellt.
