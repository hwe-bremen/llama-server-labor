# Anforderung: paket_vollstaendig

Verbindliche Vorgabe von Hawe, woertlich. Spec, Umsetzung und Review werden an diesem Text gemessen;
die Spec ist ein Loesungsvorschlag und kann falsch sein. Nur Hawe aendert diese Datei.

## Aufgabe

> Das automatische Review (review-auto) ist blind, weil das Review-Paket oft keinen Code enthält. kette.py paket nimmt nur Dateien, die die Übergabe nennt, und lässt tests/ und role-split/ grundsätzlich weg. Im echten Lauf am K7-Stand haben deshalb beide Review-Läufe A4/A5 fälschlich als „nicht umgesetzt“ gemeldet. Das soll sich ändern:
> 1. kette.py paket <kurztitel> nimmt alle Code-Dateien auf, die seit dem Rücksetzpunkt geändert oder neu sind: Commits, nicht committete Änderungen und neue, noch nicht versionierte Dateien. Auch unter tests/ und role-split/. Weggelassen werden nur docs/ und die Dateien, die die Kette selbst erzeugt (Spec, Übergabe, Verdikte usw.).
> 2. Dateien, die geändert sind, aber in der Übergabe nicht genannt werden, kommen trotzdem ins Paket, aber deutlich markiert als „nicht in der Übergabe genannt – möglicherweise außerhalb des Auftrags oder fremder Commit“.
> 3. Bleibt das Paket zu groß, wird nach Vorrang gekürzt: erst Code, dann Tests, dann Testdaten (z. B. .eml, .json). Was gekürzt oder weggelassen wurde, steht ausdrücklich im Paket. Nie still weglassen.
> 4. Steht im Paket trotzdem „keine Code-Dateien“, obwohl es Änderungen gibt, ist das ein lauter Fehler, kein stilles Ergebnis.
> 5. gegenprobe berücksichtigt nach derselben Regel auch role-split/kette/.
> Bestehende Tests in role-split/kette/test_kette.py müssen grün bleiben oder bewusst angepasst werden, wenn sie das alte Verhalten festschreiben. Abnahme: echter Lauf review-auto mail_server_test, A4/A5 dürfen nicht mehr als fehlend gemeldet werden, und das Paket nennt agents/mail_planung/mail_planung.py und die Dateien unter tests/mail_server_test/.
> Lies NUR zwei Dateien: diese Anforderung und docs/projekt_management/spec_paket_20261025_paket_vollstaendig.md (alle nötigen Codestellen mit echten Zeilennummern und gemessenen Fakten). Weitere Stellen nur, wenn wirklich etwas fehlt: search_files, dann read_file mit start_line/end_line, höchstens drei Mal.

## Antworten auf Rueckfragen

**2026-10-25 19:00** — Frage: - **(b)** Die Paketgröße überschreitet 80 000 Zeichen → kürze nur, was **nicht** zur Abnahme gehört (also keine `agents/mail_planung/`, keine `tests/mail_server_test/`-Dateien), und die Abnahme-Dateien bleiben immer drin?

> Puh, das sind ja zwei unlösbare Probleme, was würdest du vorschlagen?

**2026-10-25 19:06** — Frage: **Eine Rückfrage, die das Ergebnis ändert:** Ist `agents/` immer Produktionscode, oder gibt es unter `agents/` auch Test- oder Infrastrukturcode, der nicht zum Auftrag gehört? Wenn ja, muss die Vorrang-1-Regel feiner sein. Wenn nein, ist „unter `agents/` = Vorrang 1" eine saubere, einfache Regel.

> Ich nehme deine zweistufige Kürzung, mit diesen Änderungen:
>
> Vorrang 1, nie weglassen: alle Dateien aus der Übergabe und alle geänderten Dateien außerhalb von tests/, also agents/, scripts/, role-split/ (dort auch .md-Prompts und Rollen), mcp-server/. agents/ ist nicht nur Produktionscode, dort liegt z. B. auch test_imap_server.py. Darum die Trennung „außerhalb oder innerhalb von tests/“.
> Vorrang 2: Testcode unter tests/ (.py, .sh).
> Vorrang 3: alles andere unter tests/, also Testdaten wie .eml und .json.
> Über 80 000 Zeichen: zuerst Vorrang 3, dann Vorrang 2 als ganze Dateien weglassen, jeweils mit Liste im Paket („weggelassen: <datei> – <Grund>“). Die bestehende Begrenzung pro Datei (Diff bzw. Zeilenzahl) bleibt.
> Harte Obergrenze: Ist das Paket auch nach dem Kürzen größer als eine einstellbare Grenze (Vorgabe 150 000 Zeichen, Variable z. B. KETTE_PAKET_MAX), bricht paket mit Exit 1 und klarer Meldung ab: „Paket passt nicht in den Kontext des Review-Modells, Review in Teilen nötig.“ Kein stilles Abschneiden.
> Markierung „nicht in der Übergabe genannt“ gilt weiterhin für jede Datei, die die Übergabe nicht nennt, auch für Vorrang 1.

**2026-10-25 19:32** — Frage: 2. Ist 150 000 Zeichen die richtige Obergrenze, oder soll sie niedriger sein?

> 150 000 Zeichen bleibt als Vorgabe, einstellbar über `KETTE_PAKET_MAX` (Messung K7: ~3 Zeichen/Token, der Rahmen steckt schon im Paket). Keine harte „muss immer drin"-Liste. Fremde Commits: Die Kette erkennt ihre eigenen Commits am Kurztitel in der Commit-Nachricht; Dateien, die nur in fremden Commits geändert wurden, werden nur namentlich aufgelistet (mit Commit, markiert, ohne Inhalt) – außer die Übergabe nennt sie.
> (Von Claude nach Hawes Zustimmung am 25.10. 19:43 eingetragen; ersetzt eine versehentlich mitgeschriebene Terminal-Ausgabe.)
