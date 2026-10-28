"""Einsortieren: flache PM-Dateien in Ordner <kurztitel>/ verschieben."""
import re

import kette

TYPEN = ("spec", "spec_paket", "anforderung", "quellen", "handover",
         "pruefung", "review_paket", "verdict", "gesamt", "umsetzung",
         "nacharbeit")

TYP_MUSTER = "(?:" + "|".join(re.escape(t) for t in TYPEN) + ")"
DATEI_RE = re.compile(
    rf"^({TYP_MUSTER})_(\d{{8}})_([a-z0-9_-]+)\.md$")


def zuordnen(name: str, kurztitel_liste: list[str]) -> str | None:
    """name nach Typ+Datum+Kurztitel auflösen; laengster Treffer gewinnt."""
    m = DATEI_RE.match(name)
    if not m:
        return None
    typ, _datum, rest = m.groups()
    if typ not in TYPEN:
        return None
    treffer = []
    for kt in kurztitel_liste:
        if rest == kt or rest.startswith(kt + "_"):
            treffer.append(kt)
    if not treffer:
        return None
    return max(treffer, key=len)


def ketten() -> list[str]:
    """Sortierte Kurztitel aller flachen spec_*/anforderung_*-Dateien."""
    pm = kette.PM
    kt_set: set[str] = set()
    muster = re.compile(r"^(?:spec|anforderung)_\d{8}_([a-z0-9_-]+)\.md$")
    for p in pm.glob("*.md"):
        m = muster.match(p.name)
        if m:
            kt_set.add(m.group(1))
    return sorted(kt_set)


def einsortieren(kurztitel: str | None) -> int:
    """Flache PM-Dateien in Ordner <kurztitel>/ verschieben."""
    pm = kette.PM

    # G4.1: ungueltiger Kurztitel → Exit 2
    if kurztitel is not None:
        if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
            print(f"Ungueltiger Kurztitel: {kurztitel}")
            return 2

    alle_kt = ketten()
    if kurztitel is not None:
        if kurztitel not in alle_kt:
            alle_kt.append(kurztitel)
        alle_kt = sorted(set(alle_kt))

    had_conflict = False
    conflict_count = 0
    moved_files: set[str] = set()
    moved_folders: set[str] = set()

    for p in sorted(pm.glob("*.md")):
        name = p.name

        # Vorlagen bleiben flach
        if name.startswith("_vorlage_"):
            continue

        kt = zuordnen(name, alle_kt)
        if kt is None:
            continue

        # Nur die angeforderte Kette (wenn angegeben)
        if kurztitel and kt != kurztitel:
            continue

        ziel = pm / kt / name
        if ziel.exists():
            print(f"  ZIEL BELEGT {name} -> {kt}/ (nichts verschoben)")
            had_conflict = True
            conflict_count += 1
        else:
            kt_dir = pm / kt
            kt_dir.mkdir(parents=True, exist_ok=True)
            p.rename(ziel)
            print(f"  verschoben  {name} -> {kt}/")
            moved_files.add(name)
            moved_folders.add(kt)

    # Flache .md zaehlen (ohne Vorlagen) – erst nach allen Verschiebungen
    flat_count = sum(
        1 for p in pm.glob("*.md")
        if p.is_file() and not p.name.startswith("_vorlage_")
    )

    print()
    print(f"{len(moved_files)} Datei(en) in {len(moved_folders)} Ordner verschoben, "
          f"{conflict_count} Ziel(e) belegt, {flat_count} Datei(en) bleiben flach.")

    if moved_files:
        print()
        print("git add -A docs/projekt_management && git commit -m \"Ablage: einsortiert\"")

    return 1 if had_conflict else 0
