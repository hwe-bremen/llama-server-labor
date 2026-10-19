# Echter Projekt-Review mit12GiBCache: Einsatzentscheidung

## 3. Kein ausreichender Zusatznutzen erkennbar

Diese Entscheidung gilt für **diesen konkreten Review mit dem getesteten Qwen3.6-35B-A3B/Slipstream-Profil**. Die neue Anfrage lief9min06s, mit Modellladen insgesamt etwa11min19s. Sie liefert dieselbe unvollständige, repetitive und teilweise unrichtige Antwort wie die alte2GiB-Anfrage. Es gibt keinen validierten eingeführten Fehler und kein korrekt abgeschlossenes leeres Reviewurteil. Der menschliche Gegenprüfungsaufwand überwiegt den verwertbaren Beitrag.

Die Technik ist deutlich schneller geworden; eine fachliche Verbesserung ist bei diesem Paar explizit nicht eingetreten. Daraus folgt kein allgemeines Urteil über Slipstream, Qwen oder Haiku.

## Unveränderter Fall

Zielcommit f58b4e67d6bf24fd870e6d57ec8de6d71d624ff5, direkte Basis1a1bd6b0c7cc4553ae813ebc42ed0d49ff762f27. Zusammenhängender Teilumfang: Modellkürzel-Änderung in role-split/role_proxy.py und den zugehörigen Tests in role-split/test_role_proxy.py; andere Committeile ausgeschlossen. Vollständiger Proxy, vollständige relevante Testklasse und Konvention des Verdikt-Dateinamens im Kontext.

Die gesamte Request-Payload stimmt mit Baseline real_review_model_tags/runs/20261017T181920893653Z überein. Alle Frozeninputs unverändert, Snapshots byteidentisch. Alle Engineargumente identisch außer --pgrn-cache-gb2->12. Originalauftrag unverändert belassen, keine Lösungshinweise, Vorbefunde oder alte Antworten übermittelt. Neue Unterhaltung ohne Tools/Gedächtnis.

## Originalbefund und Validierung

Die Originalantwort steht unverändert in answer.txt; SHA-256 `70e630359a3b20ae990924e45f74b845f162d82661fce456e9d71161fb1269c8`. **Sie ist bytegenau identisch mit der2GiB-Baseline**, nicht lediglich ähnlich. Auch beide Antworten enden an derselben Stelle nach4096Tokens.

Qwen kündigt drei Fehler an, schreibt tatsächlich aber an nur einem begonnenen Befund weiter:

> Falsches Modellkürzel bei Modellen mit mehreren Größenangaben (Hoch)

Die behauptete Ursache in role_proxy.py:115 ist die Auswahl der ersten Größenangabe. Für Mellum2-12B-A2.5B entsteht mellum2-12b, für Qwen3.6/3.8 und Gemma26/31 entstehen die dokumentierten vorgesehenen Kürzel. Eine falsche Dateizuordnung oder sonstige konkrete Auswirkung ist nicht belegt. Qwen bestätigt das im Text mehrfach selbst, kehrt aber trotzdem zur Fehlersuche zurück, etwa „Ich muss einen Fehler finden“. Der Auftrag erlaubte ausdrücklich ein leeres Ergebnis.

**Bestätigte eingeführte Fehler: keine.**

**Fehlalarm:** Der als Hoch angekündigte Fehler ist für die konkret genannten Modelle widerlegt. Die Antwort behauptet darüber hinaus falsche Ausgaben für ihre erfundenen Beispiele: foo-10B-20B-test wird tatsächlich foo10b20btest, nicht foo-10b; foo-1.5b-2.0b wird foo15b20b, nicht foo-1.5b. Diese Namen verwenden den Unknown-family-Fallback. phi-3.1 wird phi31, nicht phi3.1. Das sind Fehler der Reviewbegründung.

**Ungeklärte Aussagen:** Beliebige unkonventionelle Modellnamen wurden nicht vollständig spezifiziert oder getestet; allgemeine Robustheitsvermutungen sind daher kein bestätigter eingeführter Bug. Die nicht existierende Fortsetzung nach dem Abschneiden wird nicht bewertet. Es gibt keinen zweiten/dritten abgeschlossenen konkreten Befund.

**Zusätzliche eigene Fehler:** keine im begrenzten Referenzumfang belegt. Eine korrekte leere Befundliste wäre hier ein zulässiges und potenziell nützliches Ergebnis gewesen. Die Entscheidung3 beruht auf der tatsächlichen unbelegten schweren Behauptung, Wiederholung, Begründungsfehlern und fehlendem Abschluss, nicht auf einer Pflicht, Fehler zu finden.

## Referenzprüfung und Unabhängigkeit

Die Originalantwort wurde gespeichert, bevor die Bewertung erfolgte. Referenzwissen und die frühere Antwort waren bereits bekannt; die Bewertung ist ausdrücklich **nicht blind oder unabhängig**. Wegen byteidentischer Antwort und unveränderter Snapshotquellen bleiben die früheren Belege gültig. Vorhandene relevante Tests: Basis21/Ziel22 bestanden, vollständige Originalausgaben im Baselineverzeichnis. Keine unnötige Wiederholung der ganzen Suite;8gezielte Funktionsaufrufe zur neuen Validierung in reference-reuse-checks.json bestehen. Keine Socketintegration/Vollsuite behauptet.

Für die Verifikation wurde nur vertrauenswürdiger Snapshotcode importiert; keinerlei Modelltext als Befehl ausgeführt. Kein Lösungswissen an die getestete Instanz gegeben. Ein echter Änderungsausschnitt, ein Lauf pro Cacheprofil, kein repräsentativer Benchmark.

## Messwerte

| Größe | Baseline2GiB | Neuer12GiB-Lauf |
|---|---:|---:|
| Eingabetokens | 9843 | 9843 |
| Eingabeverarbeitung, s | 722,77 | 282,40 |
| Erster sichtbarer Text, s | 722,78 | 282,42 |
| Native Eingaberate, Tokens/s | 13,62 | 34,85 |
| Generierte Tokens | 4096 | 4096 |
| Native Decoderate, Tokens/s | 5,47 | 15,53 |
| Anfrage gesamt, s | 1471,15 | 546,15 |
| Laden bis health, s | 126,67 | 132,67 |
| Laden plus Anfrage, s | 1597,81 | 678,82 |
| Expertenarena, MiB | 2046,03 | 12287,16 |
| Native Experten-Misses | 1933123 | 334855 |
| Peak Prozess-RSS, GiB | 6,74 | 16,74 |
| Zusätzliche Swapouts | 0 | 0 |
| Finish | length | length |
| Vollständiger Review | nein | nein |

Gesamte Anfrage etwa2,69fach schneller; Eingaberate2,56fach, Decode2,84fach. Experten-Misses rund82,7%geringer. Damit ist die positive Cachewirkung jetzt auch an diesem9843TokenProjektkontext gemessen; keine bloße Hochrechnung aus dem kurzen Geschwindigkeitstest.

GGUF extern, aktive PGRN intern, bewährteEngine, Reserve8GiB, Kontext16384, Batch/UBatch32,IO1,MTP4, Temp0/Seed42, kein Promptcache(cache_n0). Die einzige beabsichtigte Engineargumentänderung wurde nachträglich bestätigt. Betriebssystem-Dateicache unkontrolliert, zwei zeitlich getrennte Läufe; kein statistisch replizierter Leistungsbenchmark oder isolierter Vergleich gegen Qwen3.8.

## Denktext und Abbruchursache

Denkmodus off, Denkbudget0, reasoning-formatdeepseek, request enable_thinking=false. API liefert leeren separaten Reasoningstring und keinen separaten Reasoning-/Finaltokenzähler. Gemessen sind4096completion_tokens; alle zurückgegebenen Textstücke stehen in content. Daraus keine erfundene Messung von0internenDenktokens ableiten. Sichtbare Selbstkorrekturen verbrauchen das Ausgabelimit.

Der Client erhielt reguläres SSE-DONE, error=null und finish_reason=length. Anschließend beendet er sich absichtlich mit Fehlerstatus, weil der Review unvollständig ist. Deshalb meldet der Starter API-Anfrage fehlgeschlagen/NICHTBESTÄTIGT. **Kein belegter HTTP-, Engine-Start-, Timeout- oder Speicherfehler.** Das Kontextfenster war ausreichend:13939Gesamttokens unter16384. Der Text hat1384Whitespace-Wörter und überschreitet die gewünschte ungefähr500Wörter-Antwort deutlich. Kein automatischer Retry oder Budgetwechsel vorgenommen.

## Speicher und Bereinigung

Beobachtetes Prozess-RSSmax16,74GiB; nicht gesamter Unified-Memory-Verbrauch. Swapout-Zähler in allen Proben und vor/nachher13528351. Bereits vorhandener Swap blieb4814,31MiB. Native Cachegröße bestätigt nahezu12GiB, Highwater12377,17MiB.

EngineExit0, kein Safety-Abbruch oder Zwangscleanup,8083nachherfrei. Labor blieb gestoppt, Arbeitsdateien/Index/HEAD unverändert; aktuelle Portnachprüfung ebenfalls ohne relevante Laborlistener. Kein weiteres Modell gestartet, keine Installation, Downloads, Konvertierung oder Codekorrekturen.

## Konsequenz

Den Reviewer-Versuch mit **diesem Modell und diesem Profil** hier abschließen: schneller, aber kein ausreichender Zusatznutzen im geprüften Einsatz. Slipstream/Artefakte als technisch funktionierendes Experiment erhalten; keine automatische Erweiterung oder weiterer Wiederholungslauf. Künftige andere Modelle/Aufgaben könnten anders ausfallen, sind durch diesen Versuch aber weder freigegeben noch bewertet. Keine allgemeine Haiku-Gleichwertigkeit.
