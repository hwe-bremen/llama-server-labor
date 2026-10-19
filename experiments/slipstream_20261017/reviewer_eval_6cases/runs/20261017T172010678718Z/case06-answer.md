Hier ist die Analyse des bereitgestellten Codes `cache.py` basierend auf den Rahmenbedingungen.

### Zusammenfassung
Es wurden **keine nachgewiesenen logischen Fehler** gefunden, die die Korrektheit des Cache-Verhaltens unter den gegebenen Bedingungen (ein Prozess, ein Eventloop, feste Mandanten) verletzen. Das Design ist für den beschriebenen Anwendungsfall (LRU-Cache mit Epoch-basierter Invalidierung und Lock-Schutz) konsistent.

Es gibt jedoch ein **Designrisiko** bezüglich der Skalierbarkeit und Wartbarkeit, das nicht als "Fehler" im Sinne einer falschen Berechnung gilt, aber die Robustheit beeinträchtigen kann.

---

### Befund 1: Designrisiko – Fehlende Validierung der Mandanten-ID im `get`-Methodenaufruf

*   **Datei:** `cache.py`
*   **Stelle:** Zeile 18–20 (`async def get(...)`) und Zeile 21 (`epoch = self._epoch[tenant]`)
*   **Auslöser:** Die Methode `get` erwartet einen `tenant`-String. Die Rahmenbedingungen sagen: "Ungültige Mandanten-IDs werden vorher in der API abgewiesen."
*   **Auswirkung:** Wenn diese Vorbedingung (API-Validierung) jemals umgangen wird (z.B. durch direkten Aufruf von `ContextCache.get` in Tests oder anderen Modulen), wirft Zeile 21 eine `KeyError`, da `tenant` nicht in `self._epoch` existiert.
*   **Begründung:**
    *   **Nachweis:** `self._epoch` ist ein Dictionary, das nur die in `__init__` registrierten `tenants` enthält. Ein Zugriff auf einen nicht existierenden Schlüssel löst eine `KeyError` aus.
    *   **Einschätzung:** Dies ist kein Fehler im *aktuellen* Betriebsmodus, da die Rahmenbedingungen explizit garantieren, dass ungültige IDs vorher abgewiesen werden. Es ist jedoch ein **Designrisiko**, da die Klasse keine defensive Programmierung für den Fall eines fehlerhaften Aufrufers bietet. Eine `KeyError` ist hier schwerer zu debuggen als eine explizite `ValueError` oder `TenantNotFoundError`.
    *   **Status:** Vermutung/Risiko (keine Verletzung der Spezifikation, da Vorbedingung erfüllt sein muss).

---

### Befund 2: Kein Fehler – Korrekte Handhabung der Epoch-Invalidierung

*   **Datei:** `cache.py`
*   **Stelle:** Zeile 34–39 (`async def invalidate(...)`)
*   **Auslöser:** Aufruf von `invalidate(tenant)`.
*   **Auswirkung:** Alle Einträge für diesen Mandanten werden aus dem Cache entfernt, und die Epoch wird inkrementiert.
*   **Begründung:**
    *   **Nachweis:** Die Logik ist korrekt.
        1.  `self._epoch[tenant] += 1` stellt sicher, dass *neue* Lesezugriffe (die die alte Epoch lesen würden) als veraltet gelten.
        2.  Die Schleife `for key in list(self._values): ... del self._values[key]` entfernt physisch die alten Einträge.
        3.  Die Verwendung von `list(self._values)` ist notwendig, um während der Iteration über die OrderedDict-Elemente zu löschen, ohne eine `RuntimeError` zu verursachen.
    *   **Konsistenz mit Rahmenbedingungen:** "Bereits laufende Aufrufe dürfen ihren begonnenen Snapshot zurückgeben".
        *   Ein laufender `get`-Aufruf hat die `epoch` vor dem Lock-Halten (Zeile 21) gelesen.
        *   Wenn `invalidate` dazwischen kommt, wird die Epoch erhöht.
        *   Der laufende `get`-Aufruf prüft in Zeile 27 `if self._epoch[tenant] == epoch`. Da die Epoch sich geändert hat, wird das Ergebnis *nicht* in den Cache geschrieben (Zeile 28 wird übersprungen).
        *   Das Ergebnis wird trotzdem zurückgegeben (Zeile 32), da es bereits berechnet wurde.
        *   Dies entspricht exakt der Anforderung: "Bereits laufende Aufrufe dürfen ihren begonnenen Snapshot zurückgeben; veraltete Resultate dürfen danach nicht neu im Cache verbleiben."
    *   **Status:** Kein Fehler.

---

### Befund 3: Kein Fehler – Korrekte Lock-Nutzung und Race-Condition-Vermeidung

*   **Datei:** `cache.py
