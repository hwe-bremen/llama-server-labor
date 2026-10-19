# Ursachenanalyse der Slipstream-Reviews mit2 und12GiBCache

Stand18.10.2026. Keine neue Inferenz, kein Serverstart, keine Änderungen am
bestehenden Labor. Ausschließlich gespeicherte Requests/Antworten, /props,
Engine-Hilfe/Logs und bereits lokal gespeicherte GGUF-Metadaten gelesen.

## Zuerst die Modellidentität

Die beiden analysierten Reviewläufe sind **keine GLM-4.5-Air-Läufe**. Beide
Enginekommandos und /props.model_path zeigen
Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf. Metadaten: general.name Qwen3.6-35B-A3B,
architecture qwen35moe, etwa35,5MilliardenParameter. GLMwar zuvor durch die
Expertentyp-/PGRN-Split-Problematik blockiert (ENTSCHEIDUNG_GLM_SLIPSTREAM.md).
Diese beiden Antworten erlauben somit keine Beurteilung eines GLM-Reviews.

Analysierte Läufe:

- 2GiB: real_review_model_tags/runs/20261017T181920893653Z
- 12GiB: real_review_model_tags_12gib/runs/20261017T211054421177Z

## 1. Tatsächliches Chat-Template

**Belegt:** Beide gespeicherten /props-Antworten liefern exakt dasselbe8057Zeichen
lange Jinja-Template. Es ist bytegleich mit tokenizer.chat_template aus dem
bereits gespeicherten GGUF-Header qwen_reference/metadata/qwen.header.
SHA-256:55d4931433fe502b794226ee7f4d206a6bdd436ac9f80eb7d8ebb4c639f9ea0c.
Die Metadaten wurden mit dem vorhandenen begrenzten HeaderReader ohne Lesen von
Tensorpayload geprüft. Das Template steht separat in runtime-template.jinja.

Es ist ein Qwen-ChatML-Template mit Unsloth-Ergänzungen für Developer-Rollen und
Toolcalls, <|im_start|>/<|im_end|> als Rollengrenzen und <think>-Tags für den
optionalen Thinkingteil. /props meldet BOS<|endoftext|>, EOS<|im_end|>;
GGUF-BOS-ID248044, EOS-ID248046. Kein GLM-Template und keine nachgewiesene manuelle
Templateüberschreibung. InstallierteHilfe: --jinja ist standardmäßig aktiviert;
das fehlende explizite --jinja in der Kommandozeile ist daher kein Fehler.
Engine b10116-852e7daa1, offizielles Slipstreamv0.3.4Bundle.

**Grenze:** Der konkrete gerenderte Promptstring aus /apply-template wurde in
diesen Läufen nicht separat gespeichert, nur dessen Tokenzahl. Template/
Anforderungsparameter und übereinstimmende Tokenzahlen belegen den normalen
Pfad; ein Byte-für-Byte-Beweis der finalen serverinternen Renderausgabe liegt
nicht vor. Keine laufende Engine zum Nachrendern gestartet.

## 2. Thinking-Konfiguration

**Belegt:** Kommandozeile beider Läufe:
--reasoning off, --reasoning-budget0, --reasoning-format deepseek.
Beide Requests enthalten chat_template_kwargs.enable_thinking=false.
Das gespeicherte Template prüft genau diese Variable. Fürfalse hängt es nach
<|im_start|>assistant einen leeren, bereits geschlossenen Thinkblock an:

```text
<|im_start|>assistant
<think>

</think>

```

Das ist aus der Templateverzweigung abgeleitet, kein separat mitgeloggter
Renderstring. Die Anfrage enthält nur frische System-/Usernachrichten; keine
alte Assistant-Reasoninghistorie. preserve_thinking spielt hier keine Rolle.

/props zeigt als Default Content-only/reasoning_formatnone. Das ist allein kein
Beleg, dass die CLI-Option ignoriert wurde: /props sind Initial-/Defaultwerte,
keine vollständige pro-Request-Aufbereitung. Formaler ausgeschalteter Thinking-
Zweig und Content-only-Ausgabe sind miteinander vereinbar. reasoning-format
regelt außerdem Extraktion/Format, nicht die Fähigkeit, im normalen Text weiter
zu argumentieren. Ein gesetztesThinkbudget begrenzt nicht jeden natürlichsprachigen
Selbstkorrektursatz incontent.

Beide Streams enthalten nurcontent, keinen separaten reasoning_content-Text
und auch keine sichtbaren <think>/</think>-Tags. Ein versteckter Thinkingteil als
Verbraucher der4096Tokens ist **nicht belegt**. Ebenso wenig darf daraus eine
Messung von0internenDenktokens abgeleitet werden; die API liefert keinen separaten
Reasoningtokenzähler. Die technischen Schalter sind konsistent. Eine Garantie,
dass das Modell bei Thinkingoff knapp/korrekt antwortet, folgt daraus nicht.

## 3. Sampling und weitere Decodierung

Gemeldete Serverdefaults und explizite Requestübersteuerungen:

| Parameter | Wert / Beleg |
|---|---|
| temperature | 0, in CLI, /props und Request |
| seed | 42, CLI, /props und Request |
| top_k | 20, /props; kein Requestoverride |
| top_p | ungefähr0,95, /props; kein Override |
| min_p | ungefähr0,05, /props; kein Override |
| repeat_last_n / repeat_penalty | 64 /1,0, /props |
| presence_penalty / frequency_penalty | 0 /0, /props |
| DRY-Multiplikator | 0, /props |
| mirostat | 0, /props |
| ignore_eos | false, /props |
| max_tokens der Anfrage | 4096 |

Ein vollständiger taskbezogener Dump aller Sampler fehlt. Die nicht übersteuerten
Werte sind die gespeicherten Defaults; für Temperatur und Budget liegt zusätzlich
der tatsächliche Request vor. Temperatur0 entspricht dem Greedy-/deterministischen
Profil. Neutrale Wiederholungsstrafen setzen der beobachteten Textwiederholung
keine zusätzliche Strafwirkung entgegen. Bei Greedywahl istSeed nicht dieselbe
Diversitätssteuerung wie bei stochastischem Sampling.

MTP war aktiviert: CLI draft-mtp/max4; tatsächliche Timings melden4772Drafttokens,
2901akzeptiert, in beiden Läufen identisch. Das Defaultfeld speculative.typesnone
in /props darf deshalb nicht als Beweis gegen die tatsächlich ausgeführte
MTP-Verwendung gelesen werden. Es gibt keinen Beleg, dass MTP die Textschleife
verursacht hat.

**Hypothese:** Greedydecodierung könnte die einmal eingeschlagene repetitive
Argumentationsbahn stabilisieren. Die byteidentischen Antworten sind mit dieser
Konfiguration erwartbar und kein Beweis für einen Cachefehler. DassTemperatur0
die Ursache statt nur ein verstärkender Faktor ist, wurde nicht isoliert getestet.
Kein modellindividuell optimaler Temperaturwert behauptet: Die gepinnte öffentliche
Modelcard war für diese Analyse über das Recherchewerkzeug nicht erreichbar.

## 4. Vollständigkeit des Eingabekontexts

**Belegt:** /apply-template-/Tokenize-Vorprüfung9843Tokens, APIusage.prompt_tokens9843,
nativeTiming.prompt_n9843; cache_n0. Kontext16384, generierte4096, Summe13939.
Damit waren noch2445Tokens rechnerischer Abstand zur Kontextkapazität vorhanden.
--no-context-shift gesetzt. Engine-Releasezeile meldet außerdem truncated=0.
Die Requestnachrichten sind exakt gleich und stimmen mit dem fixierten Prompt
überein. Kein abgeschnittener Eingabekontext oder Kontextüberlauf erkennbar.
Das heißt nicht, dass das Modell alle Details inhaltlich korrekt berücksichtigt.

## 5. Warum Ende bei4096Tokens?

**Direkte Ursache:** Beide Requests setzen max_tokens4096. NativeTimings und
APIusage bestätigen exakt4096generierteTokens; finish_reasonlength, danach
reguläres SSE-DONE. Es wurde das Ausgabelimit erreicht. /propsDefaultmax_tokens=-1
hebelt die explizite Requestgrenze nicht auf.

Kein Timeout: 2GiB1471,15s,12GiB546,15s, beide unter1800s. Kein Safety-Abbruch,
EngineExit0, errornull in der eigentlichen APIauswertung. Die spätere Meldung
API-Anfrage fehlgeschlagen entsteht, weil der Client auf length absichtlich mit
RuntimeError/Fehlerexit endet. Sie ist kein ursprünglicher HTTP-/Enginefehler.

Die Antwort ist trotz vollständigem Stream semantisch unvollständig; DONEbedeutet
Transportabschluss. Ein größeres Limit hätte das Abschneiden zunächst verschoben,
aber keinen fachlichen Abschluss garantiert. Der Text überschreitet mit1384Wörtern
die gewünschte ungefähr500Wörter-Antwort bereits deutlich.

## 6. Wiederholung und Ausgabeformat

**Belegt:** Wiederholt werden fachliche Prüfgedanken statt eines präzisen
abgeschlossenen Urteils: siebenmal „Vielleicht ist der Fehler“, elfmal „Korrekt.“,
einmal „Ich muss einen Fehler finden“. Das Modell behauptet einen schweren Fehler,
bezeichnet seine Beispiele dann wiederholt selbst als korrekt und sucht weiter.
Die Ankündigung dreier konkreter Fehler wird nicht eingelöst. Der Auftrag erlaubte
explizit ein leeres Ergebnis, die behauptete Pflicht, Fehler finden zu müssen,
stammt aus der generierten Antwort.

Dies ist eine semantische Wiederholungs-/Selbstkorrekturschleife, kein belegter
endloser exakter Tokenzyklus. Die Antworten der2/12GiB-Läufe sind byteidentisch,
SHA70e630359a3b20ae990924e45f74b845f162d82661fce456e9d71161fb1269c8.
Zusammensetzen jedesdelta.content genau einmal ergibt exaktanswer.txt. Es gibt
keinen Hinweis auf versehentliche doppelte Anfügung durch den Client oder einen
Formatparser, der Thoughttexte zusätzlich kopiert. Keine sichtbaren Tool-/EOS-
Markupreste oder JSON-Formatfehler.

**Kontrollbeobachtung aus vorhandenem Lauf:** Die Scout-Planungsdiskussion benutzte
dasselbe Template, dieselben Thinking-off-Schalter und Temperatur0, endete aber
regulär mitstop nach1072Tokens. Das beweist nicht fehlerfreie Konfiguration in
jedem Detail; es spricht gegen eine global kaputte EOS-/Stopbehandlung und gegen
einen unvermeidlichen Dauerschleifenfehler des Servers. Das Verhalten hängt
zumindest vom jeweiligen Prompt/Modellverlauf ab.

## Belegte Ursachen und offene Hypothesen

Belegt sind: Request-Ausgabelimit als unmittelbare Abbruchursache; repetitiver
sichtbarer Modelltext als Grund, warum keine knappe abschließende Antwort erreicht
wurde; höhere Geschwindigkeit und weniger Misses durch12GiBohne Inhaltsänderung.
Kein belegter Templatefehler, Kontextverlust, versteckterThinkingverbrauch oder
PGRN-/MTP-/Formatparserdefekt. Sampling als Verstärker und ein promptabhängiges
Festlegen auf „es müssen Fehler existieren“ sind plausible, nicht bewiesene
Ursachen der Textproduktion.

## Entscheidung über einen weiteren Test

Die bisherige Einsatzentscheidung3 bleibt bestehen: **Diese Konfiguration nicht
als zusätzlichen zuverlässigen Reviewer einsetzen.** Ein technischer Defekt,
dessen Korrektur den Review sicher reparieren würde, ist nicht nachgewiesen.
GLMalsReviewer ist anhand dieserQwen-Läufe überhaupt nicht beurteilt.

Vor einer endgültigen modellweiten Verwerfung ist genau ein kleiner gezielter
Sampling-Diagnosetest methodisch sinnvoll: zwei kurze Anfragen an dieselbe kleine,
vollständig bereitgestellte Codeprobe, identischer Prompt/Thinkingoff/12GiBCache,
identische übrige Sampler und Grenzen; nurTemperatur0gegen einen moderaten
Diagnosewert, z.B.0,2. Das ist kein behaupteter Hersteller-Optimalwert. Nur wenige
HundertAusgabetokens, keine Wiederholung des vollständigen9843TokenReviews, kein
Cache-/Template-/MTP-Mehrfachwechsel. Prüfen: Abschluss, Repetitionsmuster,
korrektes leeres oder belegtes Urteil. Ein einzelner stochastischer Treffer ist
noch keine robuste Qualitätsbestätigung; ein solcher Test kann die Hypothese nur
eingrenzen, nicht allgemeine Eignung beweisen.

**Empfehlung:** Wenn noch Ursachenklärung gewünscht ist, diesen kurzen Sampling-
Kontrast gezielt statt weiterer Vollreviews erwägen. Für den praktischen Einsatz
bleibt das Modell bis dahin ausgeschieden. Ein weiterer größerer Cache oder nur
mehr Ausgabetokens adressiert den beobachteten inhaltlichen Fehler nicht. Es wurde
hier kein Test vorbereitet/gestartet und kein Laborparameter geändert.

Die frühere Formulierung „Modell als Reviewer ausgeschieden“ ist entsprechend
begrenzt zu lesen: gescheitert ist der untersuchte Einsatz mit diesem Prompt und
Greedyprofil; alle möglichen Konfigurationen oder Modelle sind damit nicht widerlegt.
