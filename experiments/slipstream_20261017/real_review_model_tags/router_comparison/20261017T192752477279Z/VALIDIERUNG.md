# Qwen3.8 im laufenden llama-server: Reviewvergleich

**Technisch vollständig, deutlich schneller; kein eingeführter Fehler bestätigt.**
Lauf `20261017T192752477279Z`, Qwen3.8-27B Q4_K_XL bereits geladen auf dem normalen Router8080. Kein eigener Serverstart, kein Entladen/Neustart. Derselbe fixierte Auftrag, Diff und Kontext wie beim Qwen3.6-35B-Slipstream-Lauf. Vergleichsumfang: `role-split/role_proxy.py` und `test_role_proxy.py`, Ziel f58b4e6 gegen Basis1a1bd6b. Frozen-Inputs und Originalantwort-Hash geprüft.

## Originalbefunde und Validierung

Die vollständige, unveränderte Antwort steht in `answer.txt`, SHA-256 `07141e0d301c26f68672b2c1e4c1f2f795bbd591936e9f6d1cce521a3761fd5c`.

| Qwens Originalüberschrift | Bewertung |
|---|---|
| „Falsche Modellzuordnung durch Substring-Matching (Hoch)“ | Unbestätigt; wesentliche Einführungsbehauptung falsch. |
| „Fehlende Erkennung der Modellgröße bei bestimmten Namenskonventionen (Mittel)“ | Fehlalarm für angeführtes Kollisionsbeispiel. |
| „Inkonsistenz bei der Versionserkennung für \"8B\" (Niedrig/Ungewiss)“ | Kein konkreter Fehler, sondern allgemeine Robustheitskritik. |

**1 – Familienzuordnung:** Der Basiscode verwendete bereits `if fam in low`, also Substring-Matching. Es wurde nicht erst durch diesen Commit eingeführt. Tatsächlich neu sind Suche im Repo-Basisnamen, die Kombination von Version/Größe und die Familie devstral. Bei künstlichen Namen mit mehreren Familienbezeichnungen ändert der neue devstral-Eintrag die Auswahl: `Phi-3-Devstral-7B` wurde zuvor phi, nun devstral-7b. Diese Änderung ist real; ohne tatsächlich betroffenen Modellnamen und Vertrag über dessen richtige Familie belegt sie keinen Fehler. Die Familienliste dokumentiert explizit Priorität. Qwen nennt einige Voraussetzungen selbst hypothetisch/falls existierend, stellt den Befund aber trotzdem als Hoch dar. Die Schwere und ein konkreter Schaden bleiben unbelegt.

**2 – Größe nach Punkten:** Der Regex kann Teile nach Punkten ausschließen; daraus folgt nicht die behauptete Kürzelkollision. Qwens konkrete Beispiele `model-v1.27b` und `model-v1.30b` enthalten keine bekannte Familie und verwenden den Fallback. Tatsächliche Kürzel sind `modelv127b` und `modelv130b`, bereits in der Basis und unverändert im Ziel. Beide bleiben verschieden. Qwens behauptete Ableitung ohne Größenbestandteil trifft diesen Codepfad nicht. `Qwen3.6_27B_MTP` liefert ebenfalls korrekt `qwen36-27b`. Für nicht spezifizierte sonstige Namensformen bleibt die Frage allgemein offen; ein eingeführter Fehler ist damit nicht nachgewiesen.

**3 – Apertus8B:** `Apertus-8B-Instruct` liefert `apertus-8b`, die künstliche Variante `Apertus-8-8B-Instruct` liefert `apertus8-8b`. Qwen bezeichnet die Ergebnisse selbst als korrekt beziehungsweise plausibel. Komplexe Regex und nicht vollständig abgedeckte Randfälle sind allein kein Befund über einen konkreten eingeführten Fehler und waren im Auftrag ausgeschlossen. Unsicherheit ist hier immerhin ausdrücklich gekennzeichnet.

## Referenzprüfung und Grenzen

Diese Prüfung erfolgte nach Lesen der Qwen3.8-Antwort; zudem waren der erste Qwen-Lauf und dessen Referenzprüfung schon bekannt. **Nicht blind, nicht unabhängig.** Keinerlei Lösung oder Vorbefunde wurden Qwen3.8 übertragen.

Bestehende relevante Tests auf unveränderten gepinnten Snapshots: Basis21/Ziel22 bestanden, gespeicherte Ergebnisse unter `runs/20261017T181920893653Z/reference-checks.json`. Diese bereits erfolgreichen Tests wurden nicht ohne Grund wiederholt. Zusätzlich wurden die sieben oben relevanten Namen auf Basis und Ziel direkt anhand des importierten Originalcodes verglichen;14Ausgaben und überprüfte Assertions in `finding-checks.json`. Keine Modellantwort als Befehl ausgeführt. Socketintegration, Rollen-Fixture-Tests und gesamte Repository-Vollsuite nicht ausgeführt/behauptet.

Keine bestätigten eingeführten Fehler; keine zusätzlichen Fehler bei der begrenzten eigenen Referenzprüfung. Keine umfassende Fehlerfreiheitsgarantie oder allgemeine Fehlalarmquote aus diesem einzelnen Fall.

## Laufzeiten im Vergleich

| Messgröße | Slipstream Qwen3.6-35B | Router Qwen3.8-27B |
|---|---:|---:|
| Prompttokens | 9.843 | 9.843 |
| Generierte Tokens | 4.096 | 1.526 |
| Erster sichtbarer Text | 722,78s | 86,48s |
| Anfrage insgesamt | 1.471,15s | 218,90s |
| Native Prompt-Tokens/s | 13,62 | 113,84 |
| Native Decode-Tokens/s | 5,47 | 11,52 |
| Abbruchgrund | length | stop |
| Vollständig | nein | ja |
| Separater Denktext | leer | leer |
| Zusätzliche Swapouts | 0 | 0 |

Qwen3.8 beendet die Anfrage nach3min39s, gegenüber24min31s für die abgeschnittene Slipstream-Anfrage. Die gesamte Anfrage war etwa6,72mal schneller; native Decode etwa2,10mal. Die kürzere Antwort trägt zur Differenz bei, weshalb6,72 kein reiner Durchsatzfaktor ist. Die Antwort enthält633Wörter nach Whitespace-Zählung, etwas mehr als die möglichst500Wörter des Auftrags.

Dies ist **kein isolierter Vergleich von Slipstream gegen llama.cpp**: anderes Modell (35BMoE gegen27B), anderes Release/Engine, andere Kontexte (16.384/65.536), PGRN-Streaming gegen normalen geladenen Betrieb und unterschiedliche Laufzeiteinstellungen. Im Routerbericht ist `/opt/homebrew/Cellar/llama.cpp/0.6.0_1/bin/llama-server` als Binarypfad dokumentiert; eine vollständige Buildidentität wurde nicht zusätzlich erhoben. Requestseitig bei beiden Temp0/Seed42, Thinkingfalse und max_tokens4096. Andere serverseitige Sampler/Batch-/MTP-Parameter sind nicht vollständig gleichgesetzt.

Keine separate Reasoning-Tokenzahl von der API geliefert. Der separate Denktextstring ist leer; daraus folgt keine Messung interner Denkprozesse. Swapouts vor/nachher13.528.351, Differenz0. Für diesen Routerlauf wurde keine fortlaufende RSS-/Swapüberwachung aufgezeichnet, daher kein Peak-RSS oder lückenloser Speicherverlauf behauptet.

## Praktische Konsequenz

**Qwen3.8 im normalen llama-server ist für weitere Review-Erprobung die zeitlich praktikablere Basis.** Die vollständige Antwort lässt sich leichter kontrollieren; in diesem Fall wurde jedoch kein belastbarer Fehler geliefert, und der schwerste Befund behandelt eine vorbestehende Technik als neue Regression. Deshalb keine automatische Übernahme von Befunden oder Freigabeentscheidungen.

Die Streaming-Technik war zuvor technisch nachgewiesen; für das Ziel eines stärkeren Codeprüfers liefert dieser Vergleich keinen Qualitätsvorteil des getesteten Streaming-Modells. Weitere Arbeit zunächst am vorhandenen Qwen3.8 mit einem unabhängigen bekannten Fehlerfall, statt längerer Wiederholungen desselben Reviews. Kein zusätzlicher Lauf oder Modelldownload ausgeführt. Keine Haiku-Gleichwertigkeit und kein allgemeines Modellurteil.

Der Router meldete Qwen vor und nach dem Review geladen; sein Betrieb wurde durch den Client nicht verändert. Originalantwort, Stream und response.json unverändert erhalten. Diese Auswertung steht in VALIDIERUNG.md/json.
