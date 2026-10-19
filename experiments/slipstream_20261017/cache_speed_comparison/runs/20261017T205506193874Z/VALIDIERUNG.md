# Cache-Vergleich: validierter Abschluss

## Entscheidung

**Slipstream als technischen Baustein behalten. Das12GiB-Profil zeigt deutliches Geschwindigkeitspotenzial. Der Ausbau zum Code-Reviewer bleibt pausiert.**

Die frühere negative Geschwindigkeitsbewertung muss auf das bewusst knappe2GiBProfil begrenzt werden. Es war zum Nachweis tatsächlichen Streamings gewählt und bildet nicht die bestmögliche Nutzung des48GiBMac ab. Dieser Versuch liefert einen gemessenen besseren Betriebspunkt. Er rechtfertigt keinen neuen großen Download, keine GLM-Kompatibilitätszusage und keine neue Aussage über Reviewerqualität.

## Aufbau und unabhängige Nachprüfung

Lauf20261017T205506193874Z, erstA2GiB, dannB12GiB, jeweils ein frischer Prozess mit drei gleichen Anfragen. GGUF extern, aktive PGRN intern, qualifizierte Slipstream-v0.3.4-Engine. Identischer Prompt mit558Tokens, maximal128Ausgabetokens, Kontext4096, Reserve8GiB, Batch/UBatch32, IO1, MTP4, Thinkingoff, Temp0/Seed42.

Nach dem Lauf alle sechs gespeicherten Requestnachrichten gegen Frozenprompt geprüft, jeweils558Eingabe-/128Ausgabetokens, nativecache_n0. Vollständige Engineargumente verglichen: ausschließlich --pgrn-cache-gb unterscheidet sich. Originaltexte aller sechs Antworten sind byteidentisch, SHA-256 `8e9a7778f221d8fb1f71dd9c9b85218884272b0f63811dd26474b956218f9538`.

finish_reason=length war hier die absichtliche Lastbegrenzung. Die Antwort ist kein vollständiger fachlicher Review; API-Stream/DONE und gemessene Last waren vollständig. Es wurde keine Modellantwort ausgeführt.

## Ergebnisse

Median (Minimum–Maximum) der drei Requests, sofern nicht anders bezeichnet:

| Größe | A2GiB | B12GiB |
|---|---:|---:|
| Tatsächliche Arena, MiB | 2046,03 | 12287,16 |
| Eingabeverarbeitung, s | 38,32 (38,08–41,60) | 12,94 (12,91–14,90) |
| Eingaberate, Tokens/s | 14,56 (13,41–14,66) | 43,12 (37,46–43,21) |
| Erster sichtbarer Text, s | 38,33 (38,08–41,60) | 12,95 (12,92–14,90) |
| Generierung, Tokens/s | 3,95 (3,65–4,01) | 12,50 (11,80–12,68) |
| Anfrage gesamt, s | 73,17 (70,22–73,99) | 23,16 (23,05–25,75) |
| Cache-Misses je Anfrage | 80508 (80506–80808) | 12500 (12455–16241) |
| Peak Prozess-RSS, GiB | 6,44 | 16,44 |
| Zusätzliche Swapouts | 0 | 0 |
| Modellladen bis health, s | 126,63 | 126,92 |

Eingaberate etwa2,96fach, Decode etwa3,16fach; Anfragezeit rund68%kürzer. Miss-Anzahl rund84,5%geringer. Die tatsächliche Expertenarena wurde fast vollständig mit der gewünschten12GiBObergrenze zugelassen, nicht auf etwa2GiBbeschnitten.

Erste Anfrage nach frischem Engine-Start: A38,08sTTFT/3,65Tokens/s, B14,90sTTFT/11,80Tokens/s. Zweite/dritte mit wärmerer Arena: Aca39,97sTTFT/3,98Tokens/s, Bca12,94sTTFT/12,59Tokens/s (jeweils Median der beiden). Der Effekt tritt damit nicht nur in der allerletzten Anfrage auf.

## Was die Zähler aussagen

A hatte etwa77%Experten-Cache-Misses, B zunächst15,5%, späteretwa12%. Das zeigt echte zusätzliche Wiederverwendung innerhalb der größeren Arena. Der OS-Dateicache allein ändert die nativen Arena-Misszahlen nicht; die Telemetrie stützt somit einen wesentlichen Cache-Engpass der bisherigen Konfiguration.

Die geräteweiten internen Lesezähler stiegen pro Anfrage im Median um154,06GB beiA und24,01GB beiB. Ein20,13GBPGRN kann durch wiederholtes Nachladen mehrmals seine Dateigröße an Zugriffen erzeugen. Diese Blocktreiberzähler sind nicht exklusiv dem Prozess oder der PGRN-Datei zugeordnet. Auf der externen SSD waren nahezu keine Lesezugriffe in den Anfragefenstern nötig, passend zur internen aktiven PGRN; das externe GGUF-Modellladen ist ein anderes Zeitfenster.

B kam nachA; der Betriebssystem-Dateicache wurde nicht kontrolliert oder geleert. Deshalb keine vollkommen isolierte Kausalquantifizierung des Geschwindigkeitsfaktors. Cache-Miss-Rückgang, größere native Arena, weniger physische Reads und konsistent höhere Raten ergeben zusammen aber einen belastbaren technischen Hinweis auf den Engpass.

## Grenzen und Konsequenz

Nur ein Prozesspaar; drei Requests sind keine drei unabhängigen Prozesswiederholungen. Kurzer558TokenPrompt, keine Wiederholung der13772TokenScout-Analyse. Die gemessenen3x dürfen nicht einfach als garantierte3xBeschleunigung jener Langläufe übernommen werden. Größere oder andere Aufgaben können andere Experten-Arbeitsmengen benötigen. Prozess-RSS ist nicht die gesamte Unified-Memory-Belegung; aus16,44GiBRSS folgt keine allgemeine Zusage für Parallelbetrieb.

Alle sechs Texte sind identisch. Dieser Befund zeigt für den geprüften Fall eine Geschwindigkeitsänderung ohne Inhaltsänderung, aber keine bessere Analysequalität durch den größeren Cache. Die zuvor bestätigten fachlichen Fehler bleiben relevant. Auch die GLM-Expertentyp-/Split-Blockaden werden durch mehr Cache nicht gelöst. Die praktische Nutzung eines Modells oberhalb48GiBGesamtspeicher ist weiterhin nicht nachgewiesen.

**Abschluss innerhalb der freigegebenen Grenze:**12GiBals dokumentierten Kandidaten für künftige Slipstream-Versuche festhalten, keine produktive Konfiguration ändern. Technisches Experiment erfolgreich abschließen und Dateien erhalten. Reviewer-Ausbau und große Downloads bleiben pausiert. Die früheren2GiB-Leistungsmessungen gelten als Messungen dieses knappen Streamingprofils, nicht als Obergrenze der Technik.

## Bereinigung

Beide Engines Exit0, kein Safety-Abbruch oder erzwungenes Cleanup. Alle aufgezeichneten Swapout-Werte unverändert13528351. Port8083nach beiden Prozessen frei, Labor blieb gestoppt; aktuelle relevante Ports ebenfalls frei. Gitstatus weiterhin nur der vorhandene unversionierte experiments/-Baum. Keine bestehenden Dienste automatisch gestartet/gestoppt, kein weiterer Modelllauf für diese Auswertung.

Rohdaten bleiben erhalten: summary.json, ERGEBNIS.md und die A2GiB/B12GiB-Unterordner. Diese fachliche Einordnung steht in VALIDIERUNG.md/json.
