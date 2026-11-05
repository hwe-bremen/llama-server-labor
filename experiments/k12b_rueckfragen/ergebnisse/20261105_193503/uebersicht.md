# K12b-Messung 20261105_193503

- Modell: `unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL` über `http://127.0.0.1:8080` (kette._api_ruf, thinking aus)
- Temperatur: Server-Standard; max_tokens 8000; Timeout 1800 s
- Varianten: C, D (A = Kontext + Anforderung, B = + LERNREGELN heute, C = + Projektkontext vor der Spec, D = C + LERNREGELN vor der Spec)
- Stände: git_schutz 7f95f7d^, alle_tests 1faadfe^, spec_pruefen 031d296^
- Hinweis: llama-server cached gleiche Prompt-Anfänge – Wiederholungen 2/3 sind deshalb schneller.
- Bewertung der Fragen: siehe schluessel.md (Kategorien K/N/B/U/S/L).

| Kette | Var. | Nr. | Dauer s | Prompt-Tok. | Antwort-Tok. | Fragen | Form |
|---|---|---|---|---|---|---|---|
| git_schutz | C | 1 | 16 | 3991 | 568 | 3 | ok |
| git_schutz | D | 1 | 12 | 8421 | 283 | 2 | ok |
| alle_tests | C | 1 | 16 | 3948 | 554 | 3 | ok |
| alle_tests | D | 1 | 16 | 8221 | 468 | 3 | ok |
| spec_pruefen | C | 1 | 13 | 3986 | 422 | 3 | ok |
| spec_pruefen | D | 1 | 22 | 8725 | 729 | 3 | ok |
| git_schutz | C | 2 | 7 | 3991 | 299 | 2 | ok |
| git_schutz | D | 2 | 15 | 8421 | 394 | 3 | ok |
| alle_tests | C | 2 | 8 | 3948 | 374 | 3 | ok |
| alle_tests | D | 2 | 15 | 8221 | 432 | 3 | ok |
| spec_pruefen | C | 2 | 15 | 3986 | 721 | 4 | ok |
| spec_pruefen | D | 2 | 25 | 8725 | 886 | 4 | ok |
| git_schutz | C | 3 | 6 | 3991 | 262 | 2 | ok |
| git_schutz | D | 3 | 15 | 8421 | 413 | 3 | ok |
| alle_tests | C | 3 | 9 | 3948 | 441 | 3 | ok |
| alle_tests | D | 3 | 17 | 8221 | 491 | 3 | ok |
| spec_pruefen | C | 3 | 14 | 3986 | 701 | 4 | ok |
| spec_pruefen | D | 3 | 17 | 8725 | 491 | 3 | ok |
