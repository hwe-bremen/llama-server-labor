# Quellen: abnahme_k10

Maschinell und woertlich aus dem Repo geholt mit `kette.py quellen abnahme_k10` (2026-10-27 15:58, Stand `49d4a38`), nach dem Abschnitt „Quellen“ in `spec_20261027_abnahme_k10.md`.
Nicht von Hand aendern – bei Bedarf die Spec anpassen und neu erzeugen. Konstanten, Formate und Schnittstellen werden nur von hier oder aus dem Code genommen, nie aus dem Gedaechtnis.

### `docs/projekt_management/_vorlage_handover.md` (Zeilen 1–58) – Gliederung des Handovers

```markdown
 1| # Handover: <kurztitel>
 2| 
 3| - **Spec:** `docs/projekt_management/spec_<JJJJMMTT>_<kurztitel>.md`
 4| - **Datum:** <JJJJ-MM-TT>
 5| - **Modell / Werkzeug:** <z. B. Qwen3.6 27B in OpenCode, Agent „umsetzung">
 6| - **Rücksetzpunkt:** <Commit-Hash vor der Umsetzung>
 7| 
 8| ## Umgesetzt
 9| 
10| | Anforderung (Nr. aus der Spec) | Status | Wo im Code |
11| |---|---|---|
12| | 1 | erfüllt / teilweise / nicht | `datei.py`, Funktion `xy` |
13| 
14| ## Geänderte und neue Dateien
15| 
16| - `pfad/datei.py` – neu / geändert – ein Satz, was sich geändert hat
17| 
18| ## Abweichungen von der Spec
19| 
20| - <Was anders gemacht wurde und warum. „Keine", wenn keine.>
21| 
22| ## Annahmen
23| 
24| - <Was nicht in der Spec stand und selbst entschieden wurde.>
25| 
26| ## Getestet (mit echter Ausgabe)
27| 
28| Testtitel **exakt wie in der Spec** (`kette.py abgleich` vergleicht sie). Ein Test, der anders gebaut wurde, gehört zusätzlich unter „Abweichungen".
29| 
30| **T1: <Titel wie in der Spec>** – bestanden / fehlgeschlagen
31| 
32| ```
33| $ python3 -m unittest -v tests/test_<kurztitel>.py
34| <echte Ausgabe>
35| ```
36| 
37| ## Gegenprobe (führt Hawe aus, Ausgabe hier einfügen)
38| 
39| ```
40| $ python3 role-split/kette/kette.py gegenprobe <kurztitel> --commit <rücksetzpunkt>
41| <Ausgabe>
42| ```
43| 
44| ## Außenwirkung
45| 
46| - <„Keine Befehle mit Außenwirkung ausgeführt." — oder genau, was passiert ist (Versand, Netz, echte Daten).>
47| 
48| ## Hawe muss ausführen
49| 
50| - <Befehle mit Außenwirkung, die bewusst nicht ausgeführt wurden. „Nichts", wenn nichts.>
51| 
52| ## Nicht getestet
53| 
54| - <Was nicht geprüft werden konnte und warum.>
55| 
56| ## Offene Punkte / bekannte Schwächen
57| 
58| - <…>
```
