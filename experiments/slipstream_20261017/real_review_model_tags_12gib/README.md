# Genau ein echter Projekt-Review mit12GiBCache

Vorbereitet, noch keine neue Inferenz und keine vorweggenommene Entscheidung.

## Fall und Vergleichbarkeit

Wiederholung des bereits ausgeführten echten Diffreviews:
Zielcommit f58b4e67d6bf24fd870e6d57ec8de6d71d624ff5 gegen direkte Basis
1a1bd6b0c7cc4553ae813ebc42ed0d49ff762f27. Teilumfang Modellkürzel in
role-split/role_proxy.py und role-split/test_role_proxy.py; andere Commitanteile
nicht geprüft. Vollständiger Proxy, relevante vollständige Testklasse und
Projektvertrag im Prompt wie zuvor.

Baseline: ../real_review_model_tags/runs/20261017T181920893653Z.
prompt.json ist byteidentisch zum damaligen fixierten Prompt. Die Nachrichten
wurden zusätzlich mit dem tatsächlich ausgeführten Baseline-Request verglichen.
Keine neue Reviewer-Formulierung anstelle der bisherigen, keine Korrekturen oder
Referenzbefunde hinzugefügt. Der Nutzer verlangte ausdrücklich unveränderte
Aufgabenstellung und Kontext; deshalb bleibt auch der bisherige gleichwertige
längere Reviewer-Auftrag mit möglichst500Wörtern erhalten. Es ist der echte
Modellkürzel-Diffreview, nicht die spätere Scout-Planungsdiskussion.

Alle Snapshots unverändert übernommen; keine Arbeitsdateien/Git-Zustand verändert.
Private Referenzprüfungen und alte Antworten werden NICHT ins Modell übertragen.

## Einstellungen

Identischer Modell-/Engine-/GGUF-/interner PGRN-Stand. Nur --pgrn-cache-gb ändert
sich von2 auf12. Tatsächliche Arena nachher messen, Zuteilung nicht voraussetzen.
Reserve8GiB, Kontext16384, Batch/UBatch32, IO1, MTP4, Temp0/Seed42,
Thinkingoff/Budget0, Formatdeepseek, --no-context-shift, cache_prompt=false.

Die4096Ausgabetokens bleiben für den kontrollierten Vergleich erhalten. Thinking
ist geschlossen; für eine auf ungefähr500Wörter beschränkte finale Antwort ist
diese Reserve großzügig. Bisher wurden keine separaten Reasoning-Daten geliefert:
die1384Wörter/4096Tokens der Baseline bestanden aus sichtbaren wiederholten
Selbstkorrekturen. Ein größeres Budget garantiert bei diesem Verhalten keinen
Abschluss. Diesen Effekt nicht mit angeblich verstecktem Denktext erklären.

Keine Garantie der Befolgung: bei length unvollständig markieren und Ursache
aufzeichnen, keine automatische Wiederholung oder nachträgliche Budgetänderung.

## Vorprüfung und Start

Normales macOS-Terminal, wie bei den bisherigen Tests. Bekannte ps-/localhost-
Beschränkungen der Agentenumgebung nicht erneut ausgelöst. Bisherige Ports/
llama-lsof lesend in PREPARATION.json; der Starter prüft alles erneut.
Keine andere Modellinstanz, konservativ auch kein Ollama-Embeddingrunner;
Laborportsfrei. Kein automatisches Stoppen, Unload oder Neustart bestehender
Dienste. Bei Konflikt Abbruch. Gemeinsame Sperrdatei verhindert parallele eigene
Tests. Kein Modelldownload, keine Konvertierung/Engineänderung.

```bash
python3 -B '/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/real_review_model_tags_12gib/run_review.py'
```

Genau ein Engineprozess mit genau einer Review-Inferenz, keine weitere
Testvariante. Template/Tokenize-Vorprüfung macht keine Inferenz. Bis420sLaden,
bis1800sAnfrage, bis1830sClient inklusive Vorprüfung. Fortschritt alle30s auch
während Eingabeverarbeitung. Swapout-Abbruchwache, RSS-/Speicherlogs.
Cleanup nur eigener Engine/Client/caffeinate, auch beiCtrl+C. Labor bleibt aus.

## Ergebnisaufzeichnung

runs/<UTC>/answer.txt und reasoning.txt unveränderte Stringdaten; Hashwerte,
stream.jsonl, request.json und responses.json bewahren vollständige Rohdaten.
Originalantwort wird vor jeder fachlichen Auswertung gespeichert.

Eingabetokens/-zeit, TTFTfürfinalenText und ggf.Reasoning getrennt, native
Decoderate, Gesamtdauer und Finish-Grund aus API. Reasoning-/Finaltokenzahlen nur
getrennt ausweisen, wenn API sie liefert; ansonsten nichtberichtet statt erfundener0.
Native Experten-Cache-Misses, tatsächlich zugelassene Arena/Highwater ausengine.log;
PeakRSS und Swapoutverlauf ausmemory.jsonl, keine Gleichsetzung mit gesamtem
Unified-Memory-Verbrauch. report.json prüft Pipelinebereinigung, Arbeitsdateien,
Index/HEAD und nachträglich CLI-Gleichheit außerCache sowie komplettes Request-
Payload gegenBaseline. Originaldateien/Baselinereports bleiben unverändert.

Die technische INFERENZTEST-Meldung bestätigt keine Reviewerqualität. Bei
unvollständiger Antwort bleibt sie gegebenenfalls NICHTBESTÄTIGT; Details im
Clientlog/Finish-Grund unterscheiden Ausgabelimit von einem Enginefehler.

## Validierung und eine Einsatzentscheidung

Nach Lesen der gespeicherten Antwort jeden abgeschlossenen Befund gegen
Basis/Ziel/Snapshots und relevante vorhandene Tests prüfen. Vorhandene
Referenzprüfung der Baseline (21TestsBasis,22TestsZiel, dazuVerhaltensbeispiele)
nutzen; bei neuen Behauptungen nur gezielt erweitern. Keine automatische
Schlüsselwortbenotung und keine Ausführung von Modelltext. Bestätigte Fehler,
Fehlalarme und ungeklärte Aussagen getrennt dokumentieren.

Eine korrekte leere Befundliste ist zulässig; für die Referenzprüfung des
begrenzten Änderungsausschnitts ist bisher kein eingeführter Fehler belegt.
Diese Information bleibt dem Modell vorenthalten. Die Auswertung ist NICHTblind:
Auswerter kennt Baseline, Qwen3.8-Antwort und Referenzbefunde. Ein einzelner
Wiederholungslauf ist keine allgemeine Modell- oder Haiku-Aussage.

Abschließend genau eine der Nutzerentscheidungen anhand neuer Antwort und
Gesamtdauer begründen:

1. Als zusätzlicher Reviewer praktisch hilfreich: abgeschlossener fachlich
   brauchbarer Review mit validierten Befunden oder korrekt begründet leerem
   Ergebnis; praktischen Aufwand ausdrücklich beurteilen.
2. Inhaltlich hilfreich, aber noch zu langsam oder unzuverlässig: verwertbarer
   Beitrag vorhanden, relevante Zeit-/Verlässlichkeitsgrenzen.
3. Kein ausreichender Zusatznutzen erkennbar: kein belastbarer verwertbarer
   Abschluss/Fehlerbefund bzw.korrektes leeres Urteil, oder Fehlalarme und
   Gegenprüfungsaufwand überwiegen. Unvollständigkeit korrekt eingrenzen.

Bis zum tatsächlichen Lauf keine dieser Entscheidungen als neues Ergebnis
behaupten. Keine weitere Inferenz automatisch starten.
