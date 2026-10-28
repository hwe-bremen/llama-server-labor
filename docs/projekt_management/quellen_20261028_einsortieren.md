# Quellen: einsortieren

Maschinell und woertlich aus dem Repo geholt mit `kette.py quellen einsortieren` (2026-10-28 15:32, Stand `c425db1`), nach dem Abschnitt „Quellen“ in `spec_20261028_einsortieren.md`.
Nicht von Hand aendern – bei Bedarf die Spec anpassen und neu erzeugen. Konstanten, Formate und Schnittstellen werden nur von hier oder aus dem Code genommen, nie aus dem Gedaechtnis.

### `role-split/kette/kette.py` def anforderung (Zeilen 1050–1081) – Ziel der Anforderung, Ordner anlegen (G1)

```python
1050| def anforderung(kurztitel: str, aufgabe: str | None, antwort: str | None, frage: str | None,
1051|                 datum: str | None) -> int:
1052|     vorhanden = datei_suchen("anforderung", kurztitel, datum)
1053|     zitat = lambda t: "\n".join("> " + z if z else ">" for z in t.strip().splitlines())
1054|     if aufgabe:
1055|         if vorhanden:
1056|             print(f"Gibt es schon: {vorhanden} (nichts ueberschrieben; Antworten mit --antwort anhaengen)")
1057|             return 2
1058|         d = datum or dt.date.today().strftime("%Y%m%d")
1059|         abl = ablage(kurztitel)
1060|         abl.mkdir(parents=True, exist_ok=True)
1061|         ziel = abl / f"anforderung_{d}_{kurztitel}.md"
1062|         ziel.write_text(
1063|             f"# Anforderung: {kurztitel}\n\n"
1064|             "Verbindliche Vorgabe von Hawe, woertlich. Spec, Umsetzung und Review werden an diesem Text gemessen;\n"
1065|             "die Spec ist ein Loesungsvorschlag und kann falsch sein. Nur Hawe aendert diese Datei.\n\n"
1066|             f"## Aufgabe\n\n{zitat(aufgabe)}\n\n## Antworten auf Rueckfragen\n\n", encoding="utf-8")
1067|         print(f"Angelegt: {ziel}")
1068|         return 0
1069|     if antwort:
1070|         if not vorhanden:
1071|             print(f"Keine anforderung_*_{kurztitel}.md – erst mit --aufgabe anlegen"); return 2
1072|         stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
1073|         teil = f"**{stamp}**" + (f" — Frage: {frage.strip()}" if frage else "") + f"\n\n{zitat(antwort)}\n\n"
1074|         with vorhanden.open("a", encoding="utf-8") as f:
1075|             f.write(teil)
1076|         print(f"Angehaengt an {vorhanden.name}")
1077|         return 0
1078|     print("--aufgabe oder --antwort angeben"); return 2
1079| 
1080| 
1081| # ---------------------------------------------------------------- quellen
```

### `role-split/kette/kette.py` def ablage (Zeilen 97–100) – Ordner der Kette (G1, G4)

```python
 97| def ablage(kurztitel: str) -> Path:
 98|     """Ablage-Verzeichnis: docs/projekt_management/<kurztitel>/ wenn vorhanden, sonst docs/projekt_management/."""
 99|     ordner = PM / kurztitel
100|     return ordner if ordner.is_dir() else PM
```

### `role-split/kette/kette.py` def datei_suchen (Zeilen 299–309) – findet Dateien im Ordner (G4)

```python
299| def datei_suchen(typ: str, kurztitel: str, datum: str | None) -> Path | None:
300|     if datum:
301|         # Nur Ablage-Ordner der Kette (Nachbesserung 1 E2: kein Fallback mehr auf flach)
302|         abl = ablage(kurztitel)
303|         p = abl / f"{typ}_{datum}_{kurztitel}.md"
304|         return p if p.is_file() else None
305|     # Nur exakt <typ>_<JJJJMMTT>_<kurztitel>.md – sonst greift z. B. handover_..._nachbesserung2_<kt>.md (K6, 23.10.)
306|     muster = re.compile(rf"^{re.escape(typ)}_\d{{8}}_{re.escape(kurztitel)}\.md$")
307|     abl = ablage(kurztitel)
308|     treffer = sorted(p for p in abl.glob(f"{typ}_*_{kurztitel}.md") if muster.match(p.name))
309|     return treffer[-1] if treffer else None
```

### `role-split/kette/kette.py` def main (Zeilen 2108–2171) – Subparser, Weiterleitung wie bei lauf/status (G5)

```python
2108| def main(argv=None) -> int:
2109|     ap = argparse.ArgumentParser(description="Werkzeug fuer die Kette Spec -> Umsetzung -> Review")
2110|     sub = ap.add_subparsers(dest="cmd", required=True)
2111|     p = sub.add_parser("prompt"); p.add_argument("schritt", choices=SCHRITTE); p.add_argument("kurztitel")
2112|     p.add_argument("--datum"); p.add_argument("--commit")
2113|     p.add_argument("--lauf", type=int, help="Review-Lauf-Nummer (eigener Verdikt-Dateiname je Lauf)")
2114|     q = sub.add_parser("quellen"); q.add_argument("kurztitel"); q.add_argument("--datum")
2115|     n = sub.add_parser("anforderung"); n.add_argument("kurztitel")
2116|     n.add_argument("--aufgabe"); n.add_argument("--antwort"); n.add_argument("--frage"); n.add_argument("--datum")
2117|     a = sub.add_parser("abgleich"); a.add_argument("kurztitel"); a.add_argument("--datum")
2118|     u = sub.add_parser("urteil"); u.add_argument("verdikt"); u.add_argument("--anhaengen", action="store_true")
2119|     g = sub.add_parser("gegenprobe"); g.add_argument("kurztitel")
2120|     g.add_argument("--commit", required=True, help="Ruecksetzpunkt vor der Umsetzung")
2121|     g.add_argument("--timeout", type=int, default=300)
2122|     zf = sub.add_parser("zusammenfuehren", help="Befunde mehrerer Review-Laeufe mechanisch zusammenfuehren")
2123|     zf.add_argument("verdikte", nargs="+")
2124|     pk = sub.add_parser("paket", help="Review-Paket bauen (eine Datei fuers Review)")
2125|     pk.add_argument("kurztitel"); pk.add_argument("--commit"); pk.add_argument("--datum")
2126|     pr = sub.add_parser("pruefen", help="abgleich + unittest + gegenprobe, Ausgabe in Datei")
2127|     pr.add_argument("kurztitel"); pr.add_argument("--commit"); pr.add_argument("--timeout", type=int, default=300)
2128|     ra = sub.add_parser("review-auto", help="Review-Paket, zwei API-Laeufe, Verdikte, Zusammenfassung")
2129|     ra.add_argument("kurztitel")
2130|     ua = sub.add_parser("umsetzung-auto", help="Umsetzung/Nacharbeit ueber opencode run ohne TUI, danach pruefen")
2131|     ua.add_argument("kurztitel"); ua.add_argument("--nacharbeit", help="Datei mit dem Nachbesserungs-Auftrag")
2132|     tp = sub.add_parser("tests-pruefen", help="Vorgabe-Tests pruefen: Abdeckung, laedt, rot vorab")
2133|     tp.add_argument("kurztitel"); tp.add_argument("--timeout", type=int, default=300)
2134|     lf = sub.add_parser("lauf", help="Kette: Groesse -> umsetzung-auto -> review-auto -> status")
2135|     lf.add_argument("kurztitel")
2136|     st = sub.add_parser("status", help="Stand der Kette anzeigen, ohne etwas auszufuehren")
2137|     st.add_argument("kurztitel")
2138|     args = ap.parse_args(argv)
2139|     if args.cmd == "zusammenfuehren":
2140|         return zusammenfuehren([Path(v) if Path(v).is_absolute() or Path(v).exists() else PM / Path(v).name
2141|                                 for v in args.verdikte])
2142|     if args.cmd == "paket":
2143|         return paket(args.kurztitel, args.commit, args.datum)
2144|     if args.cmd == "pruefen":
2145|         return pruefen(args.kurztitel, args.commit, args.timeout)
2146|     if args.cmd == "review-auto":
2147|         return review_auto(args.kurztitel)
2148|     if args.cmd == "umsetzung-auto":
2149|         return umsetzung_auto(args.kurztitel, args.nacharbeit)
2150|     if args.cmd == "tests-pruefen":
2151|         return tests_pruefen(args.kurztitel, args.timeout)
2152|     if args.cmd == "gegenprobe":
2153|         return gegenprobe(args.kurztitel, args.commit, args.timeout)
2154|     if args.cmd == "quellen":
2155|         return quellen(args.kurztitel, args.datum)
2156|     if args.cmd == "anforderung":
2157|         return anforderung(args.kurztitel, args.aufgabe, args.antwort, args.frage, args.datum)
2158|     if args.cmd == "prompt":
2159|         return prompt(args.schritt, args.kurztitel, args.datum, args.commit, args.lauf)
2160|     if args.cmd == "abgleich":
2161|         return abgleich(args.kurztitel, args.datum)
2162|     if args.cmd == "lauf":
2163|         import automatik
2164|         return automatik.lauf(args.kurztitel)
2165|     if args.cmd == "status":
2166|         import automatik
2167|         return automatik.status(args.kurztitel)
2168|     pfad = Path(args.verdikt)
2169|     if not pfad.is_absolute() and not pfad.exists():
2170|         pfad = PM / pfad.name
2171|     return urteil(pfad, args.anhaengen)
```
