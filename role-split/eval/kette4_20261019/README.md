# Eval-Aufgabe kette4_20261019 (Prozess-Test „Spec gegen Originalanforderung")

Eingefrorener Stand von Kette 4 **vor** der Nachbesserung (Commit 31ad471): Spec und Handover ohne Nachtrag 19.10.,
Code und Tests wie von der Umsetzungs-Instanz geliefert. Lösungsschlüssel liegt NICHT im Repo.

Frage: Findet ein Reviewer mit Hawes Originalanforderung und dem Auftrag, die Spec gegen sie zu prüfen,
die Defekte, die in Kette 4 alle drei Reviewer übersehen haben?

Lauf: `start_eval.command` (ohne Gedächtnis, git_log aus), neuer Chat je Modell, eingebaute Tools aus. Prompt:

```
@review Prüfaufgabe in role-split/eval/kette4_20261019/. Lies nur Dateien in diesem Ordner, keine gleichnamigen Dateien anderswo im Repo und keine verdict-Dateien.

1. Lies zuerst anforderung_hawe.md: Das ist die verbindliche Vorgabe. Die Spec (docs/spec_…) ist nur ein Lösungsvorschlag und kann falsch sein.
2. Prüfe die Spec gegen die Anforderung: Widerspricht eine Designentscheidung, eine Begründung oder ein „akzeptiertes Restrisiko" der Spec der Anforderung? Spiel jede solche Entscheidung als Fehlerpfad durch: Was passiert konkret beim nächsten Lauf, und kommt danach jeder Eintrag genau einmal per Mail an?
3. Prüfe dann Code (agents/, scripts/) und Tests (tests/) gegen die Anforderung, nicht nur gegen die Spec. Ein Test, der falsches Verhalten als Erwartung festschreibt, ist ein Befund.

Befundtabelle genau nach docs/projekt_management/_vorlage_verdict.md. Verdikt nach docs/projekt_management/verdict_kette4replay_<modellkürzel>.md
```

Danach: `python3 role-split/kette/kette.py urteil docs/projekt_management/verdict_kette4replay_<kürzel>.md --anhaengen`
