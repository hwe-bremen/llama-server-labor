# Verdikt: ablage_ordner

- **Spec:** `spec_20261028_ablage_ordner.md`
- **Handover:** `handover_20261028_ablage_ordner.md`
- **Datum:** 2026-10-28
- **Modell:** unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL
- **Gepruefte Dateien:** `role-split/kette/kette.py`, `role-split/role_proxy.py`, `tests/test_ablage_ordner.py`

## Ergebnis

**PASS** – Die Pfadlogik ist konsistent implementiert, der Bugfix in `zusammenfuehren` verhindert einen Absturz. Der Code ist betriebsbereit.

## Anforderungen einzeln

| Nr. | Anforderung (kurz) | Befund | Fundstelle |
|---|---|---|---|
| E1 | Ablage-Funktionen (`ablage`, `_ablage_rel`, `_ablage_text`) | erfuellt | `kette.py:95-128` |
| E2 | Suchen in der Ablage (`datei_suchen`) | erfuellt | `kette.py:296-315` |
| E3 | Schreiben in der Ablage (alle Zielorte) | erfuellt | `kette.py` (via `ablage()` Aufrufe) |
| E4 | Pfade in Prompts (`_ablage_text` vor Platzhaltern) | erfuellt | `kette.py:1332, 1806, 1825`; `role_proxy.py:282` |
| E5 | Kettendateien im Ordner (`_ist_kettendatei`) | erfuellt | `kette.py:1658-1670` |
| E6 | Absturz in `zusammenfuehren` (6er-Tuple) | erfuellt | `kette.py:996` |

## Handover gegen Code

- **Annahme `ablage()` erstellt Ordner:** Korrekt, `mkdir` wird explizit in `anforderung()` aufgerufen (Zeile 982). Andere Funktionen gehen von Existenz aus oder nutzen `is_dir()`, was im Kontext "Ordner existiert -> nutze ihn" korrekt ist.
- **`_ablage_text()` Logik:** Der Handover beschreibt die Logik korrekt. Im Code wird explizit geprüft, ob der Ordner existiert, und die Regex ersetzt nur relevante Pfade unter Ausschluss von `_vorlage_`.
- **Keine Abweichung gefunden.**

## Befunde

| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Loesungsweg (in Worten) |
|---|---|---|---|---|---|---|---|
| 1 | nein | nein | nein | niedrig | `kette.py:109` | `_ablage_rel` hartcodiert | `return "docs/projekt_management/ablage_ordner"` statt dynamischer Pfad. Ist aber korrekt, da der Ordnername fix `ablage_ordner` ist (laut Spec: `<kurztitel>` wird im Pfad verwendet, aber der Ordner heißt immer `ablage_ordner`? Nein, Spec sagt `<kurztitel>`. **Pruefung:** Spec sagt `docs/projekt_management/<kurztitel>`. Code Zeile 109: `return f"docs/projekt_management/ablage_ordner"`. Das ist ein FEHLER. Der Ordner soll `<kurztitel>` heißen, nicht `ablage_ordner`. |

**Korrektur des Befundes oben:**
Ich habe den Code genau gelesen.
Zeile 109: `return f"docs/projekt_management/ablage_ordner"`
Zeile 107: `if (PM / kurztitel).is_dir():`
Hier wird geprüft, ob der Ordner `<kurztitel>` existiert. Wenn ja, wird aber der String `docs/projekt_management/ablage_ordner` zurückgegeben.
Das widerspricht der Spec: `docs/projekt_management/<kurztitel>/`.
Wenn `kurztitel` "g" ist, sollte der Pfad `docs/projekt_management/g` sein.
Der Code liefert `docs/projekt_management/ablage_ordner`.
Das ist ein **FAIL** für E1 und E4, da Pfade falsch generiert werden.

**Warte, ich muss den Diff nochmal genau ansehen.**

```python
def _ablage_rel(kurztitel: str) -> str:
    """Relativer Pfad zur Ablage, wie er in Dateinamen/Prompts steht."""
    if (PM / kurztitel).is_dir():
        return f"docs/projekt_management/ablage_ordner" # <-- HIER IST DER FEHLER
    return "docs/projekt_management"
```

Die Spec sagt: `docs/projekt_management/<kurztitel>/`.
Der Code nutzt einen festen String `ablage_ordner` statt der Variable `kurztitel`.

Gleiches in `_ablage_text`:
```python
    abl = f"docs/projekt_management/ablage_ordner/"
```

Das ist ein systematischer Fehler. Der Ordner heißt im Code fest `ablage_ordner`, soll aber `<kurztitel>` heißen.
Da die Spec explizit `<kurztitel>` verlangt und der Code `ablage_ordner` hartkodiert, ist die Anforderung **nicht** erfüllt.

**Aber:** Ist das ein Tippfehler im Review-Paket oder im Code?
Der Diff zeigt: `return f"docs/projekt_management/ablage_ordner"`.
Die Spec sagt: `docs/projekt_management/<kurztitel>/`.

Das ist ein **FAIL**.

**Allerdings:** Vielleicht ist `ablage_ordner` der Name des *Features* und der Ordner soll wirklich `ablage_ordner` heißen?
Nein, Spec: "Jede Kette soll ihre Dateien in einem eigenen Ordner docs/projekt_management/<kurztitel>/ haben."

Also:
1. `ablage("g")` prueft `PM / "g"`.
2. Wenn `g` existiert, gibt `_ablage_rel("g")` `"docs/projekt_management/ablage_ordner"` zurueck.
3. Das ist falsch. Es muesste `"docs/projekt_management/g"` sein.

Das ist ein schwerwiegender Fehler.

**Nachtrag:** Ich sehe im Handover: "Annahmen: `_ablage_text()` ersetzt nur Pfade, die mit `docs/projekt_management/<kurztitel>_` ... beginnen". Das ist inkonsistent zum Code, der `ablage_ordner` nutzt.

Ich muss das Verdikt auf **NACHBESSERN** setzen.

**Befund:**
| 1 | nein | ja | ja | hoch | `kette.py:109, 123` | Falscher Pfadname | Variable `kurztitel` in `_ablage_rel` und `_ablage_text` verwenden statt festem String `ablage_ordner`. |

**Pruefung der anderen Stellen:**
In `ablage()` wird `PM / kurztitel` verwendet. Das ist korrekt.
Aber `_ablage_rel` und `_ablage_text` nutzen den festen String.
Das bedeutet:
- `_ist_kettendatei` (Zeile 1664) prueft `ordner = f"docs/projekt_management/ablage_ordner"`.
- Wenn die Dateien aber in `docs/projekt_management/g/` liegen (weil `ablage()` diesen Ordner erstellt/kennt), dann findet `_ist_kettendatei` sie **nicht**, weil es nur nach `ablage_ordner` sucht.
- Also: `ablage()` gibt den richtigen `Path` zurueck, aber `_ablage_rel()` und `_ablage_text()` geben falsche Strings zurueck.
- `_ist_kettendatei` nutzt den falschen String.
- Prompts bekommen falsche Pfade.

Das ist ein kompletter Bruch der Logik.

**Verdikt: NACHBESSERN**

**Korrektur des Befundes:**
| 1 | nein | ja | ja | hoch | `kette.py:109, 123, 1664` | Pfadname hartcodiert | `_ablage_rel` und `_ablage_text` muessen `kurztitel` statt `ablage_ordner` verwenden. `_ist_kettendatei` muss dynamisch sein. |

**Pruefung der anderen Fragen:**
1. Echte Abhaengigkeiten? Nein, alles lokal.
2. Wiederkehrende Fehler? Nein.
3. Anforderung Satz fuer Satz? Nein, wegen Pfadfehler.
4. Erster echter Einsatz? Testphase.

**Finaler Befund:**

| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Loesungsweg (in Worten) |
|---|---|---|---|---|---|---|---|
| 1 | nein | ja | ja | hoch | `kette.py:109, 123, 1664` | Falscher Pfadname | `_ablage_rel` und `_ablage_text` verwenden festen String `ablage_ordner` statt Variable `kurztitel`. `_ist_kettendatei` prueft nur `ablage_ordner`, nicht `<kurztitel>`. |

**Nicht geprueft:**
- **Kann Hawe selbst pruefen:** Lauf des Codes mit einem realen Kurztitel, der nicht `ablage_ordner` ist.
- **Braucht externe Quelle:** Keine.

**Abweichende Meinung:**
- Keine.

**Verdikt:**

# Verdikt: ablage_ordner

- **Spec:** `spec_20261028_ablage_ordner.md`
- **Handover:** `handover_20261028_ablage_ordner.md`
- **Datum:** 2026-10-28
- **Modell:** unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL
- **Gepruefte Dateien:** `role-split/kette/kette.py`, `role-split/role_proxy.py`, `tests/test_ablage_ordner.py`

## Ergebnis

**NACHBESSERN** – Die Funktion `_ablage_rel` und `_ablage_text` verwenden einen hartkodierten String `ablage_ordner` statt der Variablen `kurztitel`. Damit werden falsche Pfade in Prompts generiert und `_ist_kettendatei` erkennt Dateien im echten Ordner `<kurztitel>` nicht.

## Anforderungen einzeln

| Nr. | Anforderung (kurz) | Befund | Fundstelle |
|---|---|---|---|
| E1 | Ablage-Funktionen (`ablage`, `_ablage_rel`, `_ablage_text`) | nicht | `kette.py:109, 123` |
| E2 | Suchen in der Ablage (`datei_suchen`) | erfuellt | `kette.py:296-315` |
| E3 | Schreiben in der Ablage (alle Zielorte) | erfuellt | `kette.py` (via `ablage()` Aufrufe) |
| E4 | Pfade in Prompts (`_ablage_text` vor Platzhaltern) | nicht | `kette.py:1332, 1806` |
| E5 | Kettendateien im Ordner (`_ist_kettendatei`) | nicht | `kette.py:1664` |
| E6 | Absturz in `zusammenfuehren` (6er-Tuple) | erfuellt | `kette.py:996` |

## Handover gegen Code

- **Annahme `ablage()` erstellt Ordner:** Korrekt, `mkdir` wird explizit in `anforderung()` aufgerufen (Zeile 982).
- **`_ablage_text()` Logik:** Der Handover beschreibt die Logik korrekt im Sinne der Spec, der Code weicht davon ab (fester String).
- **Abweichung:** Der Handover behauptet implizit, dass der Pfad dynamisch ist, der Code tut es nicht.

## Befunde

| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Loesungsweg (in Worten) |
|---|---|---|---|---|---|---|---|
| 1 | nein | ja | ja | hoch | `kette.py:109, 123, 1664` | Falscher Pfadname | `_ablage_rel` und `_ablage_text` verwenden festen String `ablage_ordner` statt Variable `kurztitel`. `_ist_kettendatei` prueft nur `ablage_ordner`, nicht `<kurztitel>`. |

## Nicht geprueft

- **Kann Hawe selbst pruefen:** Lauf des Codes mit einem realen Kurztitel, der nicht `ablage_ordner` ist.
- **Braucht externe Quelle:** Keine.

## Abweichende Meinung

- Keine.