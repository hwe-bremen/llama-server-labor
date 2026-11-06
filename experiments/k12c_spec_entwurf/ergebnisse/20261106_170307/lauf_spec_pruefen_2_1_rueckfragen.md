<!-- 8.7 s, prompt 6985, antwort 433, Form: ok -->

F1: Soll „Groesse" in den Befunden der Spec-Prüfung explizit als „Hinweis" markiert werden, oder reicht es, wenn die Prüfung bei zu großer Spec einfach einen Fehler (Exit 2) zurückgibt, ohne eine spezifische Befundzeile für die Größe zu erzeugen?
  Optionen: A) Befundzeile „Groesse: Hinweis" wird erzeugt, aber wirkt nicht als Hürde | B) Nur Exit 2 bei Überschreitung, keine separate Befundzeile | C) Befundzeile „Groesse: Fehler" wird erzeugt
  Warum: Dies bestimmt, wie die Spec-Prüfung strukturiert wird und wie das Ergebnis im Verdikt erscheint. Da Hawe sagt, Groesse ist nur noch Hinweis, ist A wahrscheinlich, aber die mechanische Umsetzung (Befundzeile vs. nur Exit) muss geklärt sein.

Annahmen:
- Die Spec-Prüfung (`spec-pruefen`) wird so angepasst, dass sie die Größe der Spec prüft und bei Überschreitung einen Befund mit der Schwere „Hinweis" (oder ähnlich niedrig) erzeugt, anstatt einen harten Fehler.
- Die Funktion `groesse` aus `automatik.py` wird weiterhin genutzt, um die Größe zu ermitteln.
- Die Befundtabellen werden so angepasst, dass „Hinweis"-Befunde nicht zum Urteil „NACHBESSERN" führen.

Quellen:
- `role-split/kette/spec_pruefen.py` def pruefe – um die Prüfung zu erweitern
- `role-split/kette/spec_pruefen.py` def _abschnitte – um Befunde zu sammeln
- `role-split/kette/automatik.py` def groesse – zur Größenermittlung
- `role-split/kette/kette.py` def urteil – um das Urteil aus den Befunden zu leiten
- `docs/projekt_management/_vorlage_spec.md` – um die Spezifikation der Spec-Prüfung zu verstehen
