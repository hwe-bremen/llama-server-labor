<!-- Schritt 3, Web-UI, NEUER Chat. Danach: kette.py abgleich + urteil. -->
@review Prüf die Umsetzung zu „{kurztitel}".
1. Lies zuerst {anforderung}: Das ist die verbindliche Vorgabe. Die Spec docs/projekt_management/spec_{datum}_{kurztitel}.md ist nur ein Lösungsvorschlag und kann falsch sein.
2. Prüf die Spec gegen die Anforderung: Widerspricht eine Designentscheidung, eine Begründung oder ein „akzeptiertes Restrisiko" der Anforderung? Spiel jede solche Entscheidung als Fehlerpfad durch: Was passiert konkret beim nächsten Lauf, und ist die Anforderung danach noch erfüllt?
3. Prüf dann docs/projekt_management/handover_{datum}_{kurztitel}.md, den Diff gegen Rücksetzpunkt {commit}, den Code selbst und tests/test_{kurztitel}.py gegen die Anforderung, nicht nur gegen die Spec. Misst jeder Test, was verlangt ist? Ein Test, der falsches Verhalten als Erwartung festschreibt, ist ein Befund.
Ältere Verdikte und andere verdict-Dateien zu dieser Aufgabe nicht lesen.
Befundtabelle genau nach _vorlage_verdict.md, mit den Spalten Datenverlust / Unbemerkt / Harte Vorgabe (ja/nein) für jeden Befund.
Verdikt nach docs/projekt_management/verdict_{datum}_{kurztitel}_<modellkürzel>.md
