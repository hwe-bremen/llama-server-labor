# PGRN intern / Samsung T7

Median (Minimum–Maximum). A/B jeweils 3 neue Prozesse.
Je Prozess beide bisherigen Prompts, jeweils Limit 128; Prompt 1 prozessfrisch, Prompt 2 arena-vorgewärmt.
OS-Dateicache nicht kontrolliert; kein Kaltstart-Benchmark.

| Messgröße | A intern | B T7 |
|---|---:|---:|
| Ladezeit s | 127.13 (126.68–143.76) | 127.69 (127.13–128.64) |
| TTFT s, beide Prompts | 3.60 (3.12–4.04) | 11.90 (10.29–13.58) |
| Decode Tokens/s, beide Prompts | 5.92 (5.48–6.27) | 1.97 (1.82–2.12) |
| Anfrage gesamt s | 25.26 (24.43–26.55) | 77.05 (73.58–81.02) |
| Peak Prozess-RSS GiB | 6.48 (6.48–6.48) | 6.48 (6.48–6.48) |
| Zusätzliche Swapouts je Prozess, Seiten | [0, 0, 0] | [0, 0, 0] |
| Physische internal Reads GB/Anfrage | 44.74 (43.50–46.00) | 0.04 (0.00–0.49) |
| Physische external Reads GB/Anfrage | 0.00 (0.00–0.00) | 37.81 (36.88–38.73) |

Die kombinierte Spanne mischt zwei Prompts; die saubere Gegenüberstellung pro Prompt folgt.

| Prompt / Größe | A intern | B T7 |
|---|---:|---:|
| 1 / ttft_s | 3.19 (3.12–3.20) | 10.30 (10.29–10.69) |
| 1 / wall_s | 26.53 (25.85–26.55) | 78.14 (77.87–81.02) |
| 1 / decode_tokens_s | 5.49 (5.48–5.63) | 1.89 (1.82–1.89) |
| 1 / cache_misses_delta | 33356.00 (33356.00–33356.00) | 33356.00 (33356.00–33356.00) |
| 2 / ttft_s | 4.04 (4.00–4.04) | 13.13 (13.11–13.58) |
| 2 / wall_s | 24.46 (24.43–24.68) | 73.66 (73.58–76.22) |
| 2 / decode_tokens_s | 6.27 (6.20–6.27) | 2.11 (2.04–2.12) |
| 2 / cache_misses_delta | 30763.00 (30763.00–30763.00) | 30763.00 (30763.00–30763.00) |

Reihenfolge: A1, B1, B2, A2, B3, A3

- Externer PGRN-Pfad in allen B-Läufen belegt: True
- Positive native Cache-Misses in allen B-Anfragen: True
- Physische T7-Lesezähler steigen in allen B-Anfragefenstern: True
- Auch in allen engeren Decode-Teilfenstern: True
- Identische Engineargumente außer PGRN-Pfad: True

Gerätezähler sind echte Blocktreiberzähler, aber nicht exklusiv einem Prozess/einer Datei zugeordnet.
Leerlaufzähler und Rohsamples in summary.json und den einzelnen Läufen auswerten; Hintergrund-I/O kann mitwirken.
Bei fehlenden/mehrdeutigen Zählern bleibt der physische externe Streaming-Nachweis offen.

B/A Median-Decode: 0.333; Änderung -66.7 %.
Empfehlung: aktive PGRN intern für Geschwindigkeit; externe Ablage funktional bestanden, gemessenen Zeitnachteil beachten.

Kein Nachweis für Modelle oberhalb 48 GB, GLM oder Reviewer-/Haiku-Qualität.

## Nachprüfung der Rohdaten

Alle sechs Prozesse mit Exit0, sämtliche zwölf Anfragen mit128 tatsächlich erzeugten Tokens, keine Zwangsbeendigung oder Speicher-Abbruch. Alle Testports danach frei; Labor blieb gestoppt. Externe Kopie stimmt mit internem Referenzhash überein.

Alle sechs externen dreisekündigen Leerlaufkontrollen zeigen **0 externe Lesebytes**. In den sechs B-Anfragefenstern steigen die physischen T7-Lesezähler um **36,88–38,73 GB**, in engeren Decode-Teilfenstern um **29,02–33,00 GB**. In allen A-Anfragefenstern bleiben die T7-Lesezähler bei0. Das belegt aktive physische T7-Reads während der externen Experteninferenz und geht über einen offenen Pfad bzw. reine Arena-Misses hinaus. Die Zähler bleiben geräteweit, ohne exklusive Prozess-/Datei-Tracingzuordnung. Die Menge über20,13GB ist bei wiederholtem Nachladen aus einer größeren Expertendatei plausibel; es handelt sich nicht um zusätzliche Dateien.

**Abschlussentscheidung: aktive PGRN intern belassen.** Samsung T7 funktioniert als aktive externe Expertenablage in diesem geprüften Profil zuverlässig über drei Prozesse ohne zusätzliche Swapouts; die Generierungsrate beträgt aber nur etwa ein Drittel der internen Variante und die Anfragen dauern etwa dreimal so lange. Kein Kaltcache-, Dauerlast- oder Qualitätsversprechen. Quellenprüfung: verified-review.json, summary.json und jeweilige report.json/memory.jsonl/engine.log.
