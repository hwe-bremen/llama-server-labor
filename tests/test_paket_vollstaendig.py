"""Tests fuer Spec paket_vollstaendig (T1–T9).
Jede Methode entspricht einer Test-ID aus der Spec.
Behaviorale Tests: disposables Git-Repo, Paket-Inhalt pruefen, keine Quellcode-Inspektion.
Neue Funktionen werden innerhalb der Methode importiert, nicht am Dateianfang."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Projekt-Root fuer relative Pfade
PROJ_ROOT = Path(__file__).resolve().parent.parent
KETTE_DIR = PROJ_ROOT / "role-split" / "kette"


def _setup_repo(tmp_dir: Path, files: dict[str, str], commit_msg: str = "initial") -> str:
    """Erstellt ein git-Repo in tmp_dir mit gegebenen Dateien und gibt den Commit-SHA zurueck."""
    for rel_path, content in files.items():
        p = tmp_dir / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

    subprocess.run(["git", "-C", str(tmp_dir), "init"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(tmp_dir), "config", "user.email", "test@test.com"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(tmp_dir), "config", "user.name", "Test"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(tmp_dir), "add", "-A"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(tmp_dir), "commit", "-m", commit_msg], check=True, capture_output=True)
    sha = subprocess.run(["git", "-C", str(tmp_dir), "rev-parse", "HEAD"],
                         check=True, capture_output=True, text=True).stdout.strip()
    return sha


def _add_commit(tmp_dir: Path, files: dict[str, str], commit_msg: str) -> str:
    """Fuegt Dateien hinzu, committet und gibt neuen SHA zurueck."""
    for rel_path, content in files.items():
        p = tmp_dir / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_dir), "add", "-A"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(tmp_dir), "commit", "-m", commit_msg], check=True, capture_output=True)
    sha = subprocess.run(["git", "-C", str(tmp_dir), "rev-parse", "HEAD"],
                         check=True, capture_output=True, text=True).stdout.strip()
    return sha


def _kette_modul():
    """Importiert und reloade das kette-Modul."""
    import importlib
    sys.path.insert(0, str(KETTE_DIR))
    kette = importlib.import_module("kette")
    importlib.reload(kette)
    return kette


def _spec_datei(pm_dir: Path, kurztitel: str = "testkurz", datum: str = "20260101"):
    """Erzeugt eine minimale Spec-Datei."""
    spec_name = f"spec_{datum}_{kurztitel}.md"
    (pm_dir / spec_name).write_text(
        "# Spec\n\n## Ziel\nTest\n\n## Nicht-Ziele\nKeine\n\n## Anforderungen\nA1: Test\n\n## Testplan\n### T1\n- **Erwartung**: ok\n",
        encoding="utf-8"
    )


def _anforderung_datei(pm_dir: Path, kurztitel: str = "testkurz", datum: str = "20260101"):
    """Erzeugt eine minimale Anforderungs-Datei."""
    (pm_dir / f"anforderung_{datum}_{kurztitel}.md").write_text("Anforderung\n", encoding="utf-8")


class TestPaketVollstaendig(unittest.TestCase):
    """Behaviorale Tests fuer die Anforderungen A1–A7 der Spec paket_vollstaendig."""

    # ---------------------------------------------------------------- T1
    def test_t1_fehlerpfade_von_paket(self):
        """T1: Fehlerpfade von paket (Git-Fehler, kein Spec-Commit, keine Spec, ungueltiger Kurztitel)."""
        kette = _kette_modul()

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            pm_dir = tmp / "docs" / "projekt_management"
            pm_dir.mkdir(parents=True)
            _spec_datei(pm_dir)
            _anforderung_datei(pm_dir)

            # Baseline-Commit mit "Spec testkurz"
            files = {
                "mod.py": "# mod.py\n",
            }
            sha = _setup_repo(tmp, files, "Spec testkurz")

            # Commit mit Kurztitel: aendert mod.py
            _add_commit(tmp, {"mod.py": "# mod.py geaendert\n"}, "testkurz: aenderung")

            kette.ROOT = tmp
            kette.PM = pm_dir

            # (a) Normalfall: Exit 0, Paket existiert
            ergebnis = kette.paket("testkurz", sha, still=True)
            self.assertEqual(ergebnis, 0, "T1(a): paket() sollte 0 rueckgeben")
            paket_pfad = pm_dir / f"review_paket_20260101_testkurz.md"
            self.assertTrue(paket_pfad.exists(), "T1(a): Paket-Datei sollte existieren")

            # (b) Kein Commit "Spec testkurz" => Exit 2
            falscher_sha = "0000000"
            ergebnis = kette.paket("testkurz", falscher_sha, still=True)
            self.assertEqual(ergebnis, 2, "T1(b): Kein Spec-Commit sollte Exit 2 sein")

            # (c) Keine Spec-Datei => Exit 2
            os.remove(pm_dir / "spec_20260101_testkurz.md")
            ergebnis = kette.paket("testkurz", sha, still=True)
            self.assertEqual(ergebnis, 2, "T1(c): Keine Spec sollte Exit 2 sein")

            # (d) Ungueltiger Kurztitel => Exit 2
            _spec_datei(pm_dir)  # Spec wiederherstellen
            ergebnis = kette.paket("test-kurz!", sha, still=True)
            self.assertEqual(ergebnis, 2, "T1(d): Ungueltiger Kurztitel sollte Exit 2 sein")

    # ---------------------------------------------------------------- T2
    def test_t2_paket_enthaelt_tests_und_role_split_auch_unversioniert(self):
        """T2: Paket enthaelt Dateien unter tests/ und role-split/, auch unversionierte."""
        kette = _kette_modul()

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            pm_dir = tmp / "docs" / "projekt_management"
            pm_dir.mkdir(parents=True)
            _spec_datei(pm_dir)
            _anforderung_datei(pm_dir)

            # Handover nennt nur mod.py
            (pm_dir / "handover_20260101_testkurz.md").write_text(
                "## Geaenderte und neue Dateien\n\n- `mod.py`\n",
                encoding="utf-8"
            )

            # Baseline-Commit
            files = {
                "mod.py": "# mod.py\n",
            }
            sha = _setup_repo(tmp, files, "Spec testkurz")

            # Commit mit Kurztitel: aendert mod.py
            _add_commit(tmp, {"mod.py": "# mod.py geaendert\n"}, "testkurz: aenderung")

            # Unversionierte Dateien hinzufuegen
            tests_dir = tmp / "tests"
            tests_dir.mkdir(parents=True, exist_ok=True)
            (tests_dir / "test_g.py").write_text("# test_g.py\n", encoding="utf-8")

            testdaten_dir = tests_dir / "testdaten"
            testdaten_dir.mkdir(parents=True, exist_ok=True)
            (testdaten_dir / "auspruefen.json").write_text('{"test": true}\n', encoding="utf-8")

            role_split_dir = tmp / "role-split" / "kette"
            role_split_dir.mkdir(parents=True, exist_ok=True)
            (role_split_dir / "hilfs.py").write_text("# hilfs.py\n", encoding="utf-8")

            kette.ROOT = tmp
            kette.PM = pm_dir

            ergebnis = kette.paket("testkurz", sha, still=True)
            self.assertEqual(ergebnis, 0, "T2: paket() sollte 0 rueckgeben")

            paket_pfad = pm_dir / f"review_paket_20260101_testkurz.md"
            paket_inhalt = paket_pfad.read_text(encoding="utf-8")

            # tests/ und role-split/ Dateien muessen im Paket sein
            self.assertIn("tests/test_g.py", paket_inhalt, "T2: tests/test_g.py fehlt im Paket")
            self.assertIn("tests/testdaten/auspruefen.json", paket_inhalt, "T2: tests/testdaten/auspruefen.json fehlt im Paket")
            self.assertIn("role-split/kette/hilfs.py", paket_inhalt, "T2: role-split/kette/hilfs.py fehlt im Paket")

            # Die drei Dateien ausser mod.py tragen den Hinweis "nicht in der Uebergabe genannt"
            self.assertIn("nicht in der Uebergabe genannt", paket_inhalt, "T2: Hinweis fehlt")

    # ---------------------------------------------------------------- T3
    def test_t3_handover_datei_ohne_markierung_fremde_datei_mit_markierung(self):
        """T3: Handover-Datei ohne Markierung, fremde Datei mit Markierung."""
        kette = _kette_modul()

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            pm_dir = tmp / "docs" / "projekt_management"
            pm_dir.mkdir(parents=True)
            _spec_datei(pm_dir)
            _anforderung_datei(pm_dir)

            # Handover nennt mod.py und tests/test_g.py
            (pm_dir / "handover_20260101_testkurz.md").write_text(
                "## Geaenderte und neue Dateien\n\n- `mod.py`\n- `tests/test_g.py`\n",
                encoding="utf-8"
            )

            # Baseline-Commit
            files = {
                "mod.py": "# mod.py\n",
            }
            sha = _setup_repo(tmp, files, "Spec testkurz")

            # Commit mit Kurztitel: aendert mod.py und tests/test_g.py
            _add_commit(tmp, {
                "mod.py": "# mod.py geaendert\n",
                "tests/test_g.py": "# test_g.py\n",
            }, "testkurz: aenderung")

            # Unversionierte Datei
            role_split_dir = tmp / "role-split" / "kette"
            role_split_dir.mkdir(parents=True, exist_ok=True)
            (role_split_dir / "hilfs.py").write_text("# hilfs.py\n", encoding="utf-8")

            kette.ROOT = tmp
            kette.PM = pm_dir

            ergebnis = kette.paket("testkurz", sha, still=True)
            self.assertEqual(ergebnis, 0, "T3: paket() sollte 0 rueckgeben")

            paket_pfad = pm_dir / f"review_paket_20260101_testkurz.md"
            paket_inhalt = paket_pfad.read_text(encoding="utf-8")

            # mod.py und tests/test_g.py im Paket OHNE den Hinweis
            # role-split/kette/hilfs.py MIT dem Hinweis
            self.assertIn("role-split/kette/hilfs.py", paket_inhalt, "T3: role-split/kette/hilfs.py fehlt im Paket")
            self.assertIn("nicht in der Uebergabe genannt", paket_inhalt, "T3: Hinweis bei nicht-genannter Datei fehlt")

    # ---------------------------------------------------------------- T4
    def test_t4_vorrang_kuerzung_vorrang_3_wird_weggelassen(self):
        """T4: Vorrang-Kuerzung – Vorrang 3 wird weggelassen."""
        kette = _kette_modul()

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            pm_dir = tmp / "docs" / "projekt_management"
            pm_dir.mkdir(parents=True)
            _spec_datei(pm_dir)
            _anforderung_datei(pm_dir)

            # Handover nennt mod.py
            (pm_dir / "handover_20260101_testkurz.md").write_text(
                "## Geaenderte und neue Dateien\n\n- `mod.py`\n",
                encoding="utf-8"
            )

            # Python 3.10 Kompatibilitaet: keine Backslashes in f-strings
            zeile = "y\n"

            # PAKET_DIFF_ZEILEN und PAKET_DATEI_ZEILEN temporar erhoehen, damit Dateien nicht gekappt werden
            alt_diff = kette.PAKET_DIFF_ZEILEN
            alt_datei = kette.PAKET_DATEI_ZEILEN
            kette.PAKET_DIFF_ZEILEN = 100000  # sehr hoch, damit keine Kappung erfolgt
            kette.PAKET_DATEI_ZEILEN = 100000  # sehr hoch, damit keine Kappung erfolgt
            self.addCleanup(setattr, kette, "PAKET_DIFF_ZEILEN", alt_diff)
            self.addCleanup(setattr, kette, "PAKET_DATEI_ZEILEN", alt_datei)

            # Baseline-Commit: Dateien mit Inhalt
            # Vorrang 1: ~25000 Zeichen, Vorrang 2: ~25000 Zeichen, Vorrang 3: ~30000 Zeichen
            # Gesamt: ~80000 Zeichen, also muss Vorrang 3 entfernt werden, um unter 80000 zu kommen
            files = {
                "mod.py": "# mod.py\n" + zeile * 25000,  # Vorrang 1
                "tests/test_g.py": "# test_g.py\n" + zeile * 25000,  # Vorrang 2
                "tests/testdaten/auspruefen.eml": "# Grosser Inhalt\n" + zeile * 30000,  # Vorrang 3
            }
            sha = _setup_repo(tmp, files, "Spec testkurz")

            # Aenderungen committen mit Kurztitel: alle Zeilen aendern, um groeßeren Diff zu erzeugen
            _add_commit(tmp, {
                "mod.py": "# mod.py geaendert\n" + "z\n" * 25000,  # alle Zeilen aendern
                "tests/test_g.py": "# test_g.py geaendert\n" + "z\n" * 25000,  # alle Zeilen aendern
                "tests/testdaten/auspruefen.eml": "# eml geaendert\n" + "z\n" * 30000,  # alle Zeilen aendern
            }, "testkurz: aenderung")

            kette.ROOT = tmp
            kette.PM = pm_dir

            ergebnis = kette.paket("testkurz", sha, still=True)
            self.assertEqual(ergebnis, 0, "T4: paket() sollte 0 rueckgeben")

            paket_pfad = pm_dir / f"review_paket_20260101_testkurz.md"
            paket_inhalt = paket_pfad.read_text(encoding="utf-8")

            # mod.py und tests/test_g.py im Paket
            self.assertIn("mod.py", paket_inhalt, "T4: mod.py fehlt im Paket")
            self.assertIn("tests/test_g.py", paket_inhalt, "T4: tests/test_g.py fehlt im Paket")

            # tests/testdaten/auspruefen.eml in "Weggelassen"-Sektion
            self.assertIn("weggelassen", paket_inhalt.lower(), "T4: Weggelassen-Sektion fehlt")
            self.assertIn("tests/testdaten/auspruefen.eml", paket_inhalt, "T4: auspruefen.eml fehlt in Weggelassen-Liste")

    # ---------------------------------------------------------------- T5
    def test_t5_kette_paket_max_ueberschritten_exit_1(self):
        """T5: KETTE_PAKET_MAX ueberschritten -> Exit 1."""
        kette = _kette_modul()

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            pm_dir = tmp / "docs" / "projekt_management"
            pm_dir.mkdir(parents=True)
            _spec_datei(pm_dir)
            _anforderung_datei(pm_dir)

            # Handover nennt mod.py
            (pm_dir / "handover_20260101_testkurz.md").write_text(
                "## Geaenderte und neue Dateien\n\n- `mod.py`\n",
                encoding="utf-8"
            )

            # Python 3.10 Kompatibilitaet: keine Backslashes in f-strings
            zeile = "y\n"
            riesiger_inhalt = "# Riesiger Inhalt\n" + zeile * 200000  # > 150000 Zeichen

            # Baseline-Commit
            files = {
                "mod.py": riesiger_inhalt,  # Vorrang 1, > 150000 Zeichen
            }
            sha = _setup_repo(tmp, files, "Spec testkurz")

            # Aenderung committen mit Kurztitel
            _add_commit(tmp, {
                "mod.py": "# Riesiger Inhalt geaendert\n" + zeile * 200000,
            }, "testkurz: aenderung")

            kette.ROOT = tmp
            kette.PM = pm_dir

            ergebnis = kette.paket("testkurz", sha, still=True)
            self.assertEqual(ergebnis, 1, "T5: paket() sollte Exit 1 rueckgeben bei KETTE_PAKET_MAX")

            # Keine review_paket_*-Datei
            paket_pfad = pm_dir / f"review_paket_20260101_testkurz.md"
            self.assertFalse(paket_pfad.exists(), "T5: Paket-Datei darf nicht existieren bei Exit 1")

    # ---------------------------------------------------------------- T6
    def test_t6_gegenprobe_beruecksichtigt_role_split_kette(self):
        """T6: Gegenprobe beruecksichtigt role-split/kette/."""
        kette = _kette_modul()

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            pm_dir = tmp / "docs" / "projekt_management"
            pm_dir.mkdir(parents=True)
            _spec_datei(pm_dir)
            _anforderung_datei(pm_dir)

            # Baseline-Commit
            files = {
                "role-split/kette/kette.py": "# kette\n",
                "role-split/kette/hilfs.py": "# hilfs.py\n",
                "tests/test_g.py": "import unittest\nclass T(unittest.TestCase):\n    def test_ok(self):\n        self.assertTrue(True)\n",
            }
            sha = _setup_repo(tmp, files, "Spec testkurz")

            # Aenderung an role-split/kette/ Datei mit Kurztitel
            _add_commit(tmp, {
                "role-split/kette/hilfs.py": "# hilfs.py geaendert\n",
            }, "testkurz: aenderung")

            kette.ROOT = tmp
            kette.PM = pm_dir

            # role-split/kette/ Dateien duerfen nicht ausgeschlossen sein
            diff_text, dateien, fremde, weggelassen = kette._diff(sha, None, "testkurz")

            role_split_dateien = [d for d in dateien if d.startswith("role-split/kette/")]
            self.assertTrue(len(role_split_dateien) > 0,
                            f"T6: role-split/kette/ Dateien sollten nicht ausgeschlossen sein (gefunden: {role_split_dateien})")

    # ---------------------------------------------------------------- T7
    def test_t7_bestehende_tests_in_test_kette_py_bleiben_gruen(self):
        """T7: Bestehende Tests in test_kette.py bleiben gruen."""
        # test_kette.py wird im echten Repo aufgerufen (keine temporären Repos)
        ergebnis = subprocess.run(
            ["python3", str(KETTE_DIR / "test_kette.py")],
            capture_output=True, text=True, timeout=180
        )
        self.assertEqual(ergebnis.returncode, 0,
                         f"T7: test_kette.py sollte alle Tests bestehen. Ausgabe:\n{ergebnis.stdout}\n{ergebnis.stderr}")

    # ---------------------------------------------------------------- T8
    def test_t8_fremde_commits_nur_als_liste(self):
        """T8: Fremde Commits nur als Liste."""
        kette = _kette_modul()

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            pm_dir = tmp / "docs" / "projekt_management"
            pm_dir.mkdir(parents=True)
            _spec_datei(pm_dir)
            _anforderung_datei(pm_dir)

            # Handover nennt mod.py und anderes.py
            (pm_dir / "handover_20260101_testkurz.md").write_text(
                "## Geaenderte und neue Dateien\n\n- `mod.py`\n- `anderes.py`\n",
                encoding="utf-8"
            )

            # Baseline-Commit
            files = {
                "mod.py": "# mod.py\n",
            }
            sha = _setup_repo(tmp, files, "Spec testkurz")

            # Commit mit Kurztitel: aendert mod.py
            _add_commit(tmp, {"mod.py": "# mod.py geaendert\n"}, "testkurz: mod aenderung")

            # Commit OHNE Kurztitel: aendert werkzeug.py und anderes.py
            _add_commit(tmp, {
                "werkzeug.py": "# werkzeug.py\n",
                "anderes.py": "# anderes.py\n",
            }, "Werkzeug: x")

            kette.ROOT = tmp
            kette.PM = pm_dir

            diff_text, dateien, fremde, weggelassen = kette._diff(sha, {"mod.py", "anderes.py"}, "testkurz")

            # mod.py und anderes.py mit Inhalt im Paket (anderes.py gehoert ueber die Uebergabe dazu)
            self.assertIn("mod.py", dateien, "T8: mod.py fehlt im Paket")
            self.assertIn("anderes.py", dateien, "T8: anderes.py fehlt im Paket (im Handover genannt)")

            # werkzeug.py nur in "Fremde Aenderungen (nur Liste)"
            self.assertIn("werkzeug.py", " ".join(fremde), "T8: werkzeug.py sollte in fremde-Liste sein")

    # ---------------------------------------------------------------- T9
    def test_t9_paket_ohne_code_trotz_aenderungen_exit_1(self):
        """T9: Paket ohne Code trotz Aenderungen -> Exit 1."""
        kette = _kette_modul()

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            pm_dir = tmp / "docs" / "projekt_management"
            pm_dir.mkdir(parents=True)
            _spec_datei(pm_dir)
            _anforderung_datei(pm_dir)

            # Baseline-Commit
            files = {
                "mod.py": "# mod.py\n",
            }
            sha = _setup_repo(tmp, files, "Spec testkurz")

            # Nur Commit OHNE Kurztitel (fremd)
            _add_commit(tmp, {"mod.py": "# mod.py geaendert\n"}, "Werkzeug: x")

            kette.ROOT = tmp
            kette.PM = pm_dir

            # (a) Exit 1, Meldung "Paket ohne Code trotz Aenderungen", keine review_paket_*-Datei
            ergebnis = kette.paket("testkurz", sha, still=True)
            self.assertEqual(ergebnis, 1, "T9(a): paket() sollte Exit 1 rueckgeben bei nur fremden Aenderungen")

            paket_pfad = pm_dir / f"review_paket_20260101_testkurz.md"
            self.assertFalse(paket_pfad.exists(), "T9(a): Paket-Datei darf nicht existieren bei Exit 1")

            # (b) Keine Aenderung ausser docs/ => Exit 0, "keine Code-Dateien"
            # Neues Repo fuer Fall (b)
            tmp2 = Path(tempfile.mkdtemp())
            pm_dir2 = tmp2 / "docs" / "projekt_management"
            pm_dir2.mkdir(parents=True)
            _spec_datei(pm_dir2)
            _anforderung_datei(pm_dir2)

            files2 = {
                "docs/lese_mich.md": "# Lese mich\n",
            }
            sha2 = _setup_repo(tmp2, files2, "Spec testkurz")

            # Nur docs/ Aenderung
            _add_commit(tmp2, {"docs/lese_mich.md": "# Lese mich geaendert\n"}, "docs update")

            kette.ROOT = tmp2
            kette.PM = pm_dir2

            ergebnis2 = kette.paket("testkurz", sha2, still=True)
            self.assertEqual(ergebnis2, 0, "T9(b): paket() sollte Exit 0 rueckgeben bei nur docs/ Aenderungen")


if __name__ == "__main__":
    unittest.main()
