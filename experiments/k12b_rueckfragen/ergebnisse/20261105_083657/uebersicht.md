# K12b-Messung 20261105_083657

- Modell: `unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL` über `http://127.0.0.1:8080` (kette._api_ruf, thinking aus)
- Temperatur: Server-Standard; max_tokens 8000; Timeout 1800 s
- Varianten: A = Kontext + Anforderung, B = zusätzlich LERNREGELN.md
- Hinweis: llama-server cached gleiche Prompt-Anfänge – Wiederholungen 2/3 sind deshalb schneller.
- Bewertung der Fragen: siehe schluessel.md (Kategorien K/N/B/U/S/L).

| Kette | Var. | Nr. | Dauer s | Prompt-Tok. | Antwort-Tok. | Fragen | Form | Hawe: hätte geändert? |
|---|---|---|---|---|---|---|---|---|
| git_schutz | A | 1 | 12 | 449 | 580 | 3 | ok | |
| git_schutz | B | 1 | 16 | 5456 | 467 | 2 | ok | |
| alle_tests | A | 1 | 6 | 420 | 266 | 2 | ok | |
| alle_tests | B | 1 | 15 | 5427 | 709 | 4 | F4 ohne „Optionen:“; F4 ohne „Warum:“ | |
| spec_pruefen | A | 1 | 9 | 439 | 440 | 3 | ok | |
| spec_pruefen | B | 1 | 16 | 5446 | 774 | 5 | ok | |
| git_schutz | A | 2 | 8 | 449 | 404 | 3 | ok | |
| git_schutz | B | 2 | 11 | 5456 | 516 | 3 | ok | |
| alle_tests | A | 2 | 7 | 420 | 318 | 3 | ok | |
| alle_tests | B | 2 | 8 | 5427 | 351 | 3 | ok | |
| spec_pruefen | A | 2 | 6 | 439 | 320 | 3 | ok | |
| spec_pruefen | B | 2 | 6 | 5446 | 283 | 3 | ok | |
| git_schutz | A | 3 | 6 | 449 | 297 | 2 | ok | |
| git_schutz | B | 3 | 12 | 5456 | 583 | 3 | ok | |
| alle_tests | A | 3 | 4 | 420 | 210 | 2 | ok | |
| alle_tests | B | 3 | 12 | 5427 | 594 | 3 | ok | |
| spec_pruefen | A | 3 | 9 | 439 | 435 | 3 | ok | |
| spec_pruefen | B | 3 | 21 | 5446 | 1031 | 5 | ok | |
