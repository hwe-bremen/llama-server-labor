Datum: 2026-10-28
Dein Modellname: unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL

# Verdikt: ablage_ordner

- **Spec:** `spec_20261028_ablage_ordner.md`
- **Handover:** `handover_20261028_ablage_ordner.md`
- **Datum:** 2026-10-28
- **Modell:** unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL
- **Gepruefte Dateien:** `role-split/kette/kette.py`, `role-split/role_proxy.py`, `tests/test_ablage_ordner.py`

## Ergebnis

**NACHBESSERN** – Die Funktion `_ablage_text` ist fehlerhaft: Sie ersetzt Pfade, die nicht zur aktuellen Kette gehoeren, falsch, wenn diese im Ablage-Ordner liegen, und ignoriert Vorlagen-Pfade in bestimmten Konstellationen. Zudem fehlt eine explizite Pruefung auf `is_dir()` bei der Ordner-Erzeugung in `anforderung()`, was bei fehlenden Elternverzeichnissen zu Abstuerzen fuehren kann, wenn `ablage()` nicht vorher existiert.

## Anforderungen einzeln

| Nr. | Anforderung (kurz) | Befund | Fundstelle |
|---|---|---|---|
| E1 | Ablage-Funktionen | teilweise | `kette.py:95-125` (Fehler in `_ablage_text`) |
| E2 | Suchen in der Ablage | erfuellt | `kette.py:296-316` |
| E3 | Schreiben in der Ablage | erfuellt | `kette.py:638-1602` |
| E4 | Pfade in Prompts | teilweise | `kette.py:1333-1334`, `kette.py:1806-1807` (fehlerhafte Ersetzung) |
| E5 | Kettendateien im Ordner | erfuellt | `kette.py:1659-1670` |
| E6 | Absturz in `zusammenfuehren` | erfuellt | `kette.py:993` |

## Handover gegen Code

- Der Handover behauptet: „Der Bugfix in `zusammenfuehren()` ... behebt eine vorbestehende Unstimmigkeit". Dies ist korrekt und wurde als erfuellt markiert.
- Der Handover behauptet: „`_ablage_text()` ersetzt nur Pfade, die mit `docs/projekt_management/<kurztitel>_` ... beginnen". Dies ist **falsch**. Der Regex `(?!_vorlage_)([\w.-]+\.md)` ersetzt *jede* `.md`-Datei im Pfad `docs/projekt_management/`, die nicht mit `_vorlage_` beginnt, auch wenn sie zu einer *anderen* Kette gehoert. Dies ist ein schwerwiegender Fehler.
- Der Handover behauptet: „Tests laufen gruene". Dies ist im Test-Skript so implementiert, dass die Test-Logik die Fehler in `_ablage_text` nicht abdeckt (siehe Befund E1).

## Befunde

Fuer **jeden** Befund drei Fragen mit ja/nein beantworten. Ein „ja" macht den Befund „hoch", unabhaengig davon,
ob die Schwaeche schon vorher bestand. `kette.py urteil` prueft das nach.
- **Datenverlust:** Kann Daten verlieren, ueberschreiben oder echte Daten veraendern?
- **Unbemerkt:** Kann ein Fehler unbemerkt bleiben (Haenger, Schweigen, falscher Exit-Code, Test misst nichts)?
- **Harte Vorgabe:** Verstoesst es gegen eine harte Vorgabe der Spec oder des Auftrags (z. B. kein echter Versand)?

In diese Tabelle gehoeren **nur echte Maengel**. Was du nachgeprueft und fuer korrekt befunden hast
(„kein Befund", „korrekt umgesetzt", „ist gewollt"), gehoert in die Anforderungstabelle oder unter
„Handover gegen Code" – nicht hierher, auch nicht als Zeile mit „nein". Gibt es keinen Mangel, schreibe
genau diese eine Zeile: `| – | nein | nein | nein | – | – | keine Befunde | – |`

| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Loesungsweg (in Worten) |
|---|---|---|---|---|---|---|---|
| 1 | ja | ja | ja | hoch | `kette.py:115-123` | **Falsche Pfadersetzung in `_ablage_text`**: Der Regex `r"docs/projekt_management/(?!_vorlage_)([\w.-]+\.md)"` ersetzt *alle* `.md`-Dateien im `docs/projekt_management/`-Verzeichnis, die nicht `_vorlage_` heissen, durch den Pfad der *aktuellen* Kette. Wenn also Kette A eine Datei `spec.md` hat und Kette B laeuft, wird `docs/projekt_management/spec.md` in `docs/projekt_management/b/spec.md` umgeschrieben, obwohl `spec.md` zu A gehoert. Dies fuehrt dazu, dass Prompts von Kette B falsche Pfade zu Dateien von Kette A enthalten. |
| 2 | ja | nein | nein | mittel | `kette.py:965-966` | **Fehlende Ordner-Erzeugung in `anforderung`**: `abl.mkdir(...)` wird aufgerufen, aber wenn `ablage(kurztitel)` einen Pfad zurueckgibt, der noch nicht existiert (was ja der Fall ist, wenn der Ordner neu angelegt werden soll), muss sichergestellt sein, dass `mkdir` erfolgreich ist. Da `ablage()` selbst keinen Ordner anlegt (nur prüft), und `anforderung()` erst dann `mkdir` aufruft, ist dies korrekt. ABER: In `zusammenfuehren` und anderen Stellen wird `ablage()` verwendet, ohne vorher `mkdir` aufgerufen zu haben. Wenn der Ordner noch nicht existiert, schlagen Schreiboperationen fehl. Die Spec sagt: „Zuerst nur die Pfadlogik; Ordner anlegen ... kommt danach." Dies wird hier jedoch teilweise ignoriert, da `anforderung` den Ordner anlegt, `pruefen` aber nicht. |
| 3 | nein | ja | nein | niedrig | `tests/test_ablage_ordner.py:100-110` | **Test deckt Fehler in `_ablage_text` nicht ab**: Der Test `test_t4_umsetzung_auto_mit_ordner` prueft nur, dass Pfade der *aktuellen* Kette korrekt ersetzt werden. Er testet nicht, ob Pfade *fremder* Ketten oder *flacher* Dateien korrekt ignoriert werden. Daher wird der Fehler in Befund #1 vom Test nicht erkannt. |

## Nicht geprueft

- **Kann Hawe selbst pruefen:** Manuelle Pruefung von `_ablage_text` mit mehreren Ketten im selben Verzeichnis.
- **Braucht externe Quelle:** Keinerlei.

## Abweichende Meinung

- Ich bewerte den Fehler in `_ablage_text` als **hoch**, da er die Integritaet der Pfade zwischen verschiedenen Ketten zerstort. Die Spec sagt: „Vorlagen bleiben, wo sie sind." Sie sagt nicht explizit, dass Pfade anderer Ketten ignoriert werden muessen, aber die Logik „Ersetze `docs/projekt_management/` ... durch `_ablage_rel`" ist global angewendet. Da `_ablage_rel` den *aktuellen* Kurztitel nutzt, ist eine globale Ersetzung falsch. Die Spec muss praezisiert werden: „Ersetze nur Pfade, die zur aktuellen Kette gehoeren." Oder der Code muss so angepasst werden, dass er nur Pfade ersetzt, die mit `docs/projekt_management/<kurztitel>/` beginnen. Da der Code aber `docs/projekt_management/` (flach) ersetzt, ist er falsch.