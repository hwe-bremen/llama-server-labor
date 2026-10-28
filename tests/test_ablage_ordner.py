#!/usr/bin/env python3
"""Vorgabe-Tests fuer K13a ablage_ordner (spec_20261028_ablage_ordner.md, T1–T7).

VORGABE: Diese Datei ist vor der Umsetzung geschrieben. Die Umsetzung aendert sie nicht.

Keine Aussenwirkung: T1–T3 und T5 arbeiten in tempfile.TemporaryDirectory() mit umgebogenem kette.ROOT/kette.PM;
T4 nutzt Basis aus tests/test_umsetzung_auto.py (Temp-Git-Repo, Attrappe opencode_fake.py mit Temp-Sperre,
Pruefung, dass das echte Repo unveraendert ist); T6 laedt role_proxy und biegt kette.ROOT/PM ebenso um.
Neue Funktionen werden in der Methode importiert; jede Methode hat einen Teil, der vorab rot ist.
"""
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ECHT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ECHT))
sys.path.insert(0, str(ECHT / "role-split" / "kette"))
import kette  # noqa: E402
from tests.test_umsetzung_auto import Basis, DATUM, HANDOVER  # noqa: E402

D = "20261028"


class Temp(unittest.TestCase):
    def setUp(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        self.root = Path(d.name).resolve()
        self.pm = self.root / "docs" / "projekt_management"
        self.pm.mkdir(parents=True)
        for name, wert in (("ROOT", self.root), ("PM", self.pm)):
            alt = getattr(kette, name)
            setattr(kette, name, wert)
            self.addCleanup(setattr, kette, name, alt)

    def rufen(self, fn, *a, **kw):
        aus = io.StringIO()
        with redirect_stdout(aus), redirect_stderr(aus):
            code = fn(*a, **kw)
        return code, aus.getvalue()


class Ablage(Temp):

    def test_t1_ablage_ordner_oder_flach(self):
        """T1: ablage – Ordner der Kette, wenn vorhanden, sonst flach"""
        from kette import ablage, _ablage_rel
        self.assertEqual(ablage("k"), self.pm)
        self.assertEqual(_ablage_rel("k"), "docs/projekt_management")
        (self.pm / "k").mkdir()
        self.assertEqual(ablage("k"), self.pm / "k")
        self.assertEqual(_ablage_rel("k"), "docs/projekt_management/k")
        self.assertEqual(ablage("andere"), self.pm)          # Ordner gilt nur fuer seine Kette

    def test_t2_datei_suchen_in_der_ablage(self):
        """T2: datei_suchen – sucht in der Ablage der Kette"""
        (self.pm / f"spec_{D}_k.md").write_text("flach\n", encoding="utf-8")
        self.assertEqual(kette.datei_suchen("spec", "k", None), self.pm / f"spec_{D}_k.md")   # ohne Ordner wie bisher
        (self.pm / "k").mkdir()
        (self.pm / "k" / f"spec_{D}_k.md").write_text("im Ordner\n", encoding="utf-8")
        self.assertEqual(kette.datei_suchen("spec", "k", None), self.pm / "k" / f"spec_{D}_k.md")
        self.assertEqual(kette.datei_suchen("spec", "k", D), self.pm / "k" / f"spec_{D}_k.md")
        self.assertIsNone(kette.datei_suchen("handover", "k", None))
        (self.pm / f"handover_{D}_k.md").write_text("flach\n", encoding="utf-8")       # Nacharbeit 1: kein Rueckfall
        self.assertIsNone(kette.datei_suchen("handover", "k", None))
        self.assertIsNone(kette.datei_suchen("handover", "k", D))

    def test_t3_schreibende_befehle_in_der_ablage(self):
        """T3: anforderung, Verdikt-Pfad und Gesamtbefund landen in der Ablage"""
        (self.pm / "k").mkdir()
        code, out = self.rufen(kette.anforderung, "k", "Aufgabe X", None, None, D)
        self.assertEqual(code, 0, out)
        self.assertTrue((self.pm / "k" / f"anforderung_{D}_k.md").is_file(), out)
        self.assertFalse((self.pm / f"anforderung_{D}_k.md").exists())
        self.assertEqual(kette._freier_verdiktpfad(D, "k", 2), self.pm / "k" / f"verdict_{D}_k_qwen36-35b_betrieb.md")
        v = self.pm / "k" / f"verdict_{D}_k_qwen36-35b.md"
        v.write_text("# Verdikt\n\n## Ergebnis\n\n**PASS** – ok\n", encoding="utf-8")
        code, out = self.rufen(kette.zusammenfuehren, [v], _internal=True)
        self.assertTrue((self.pm / "k" / f"gesamt_{D}_k.md").is_file(), out)
        self.assertFalse((self.pm / f"gesamt_{D}_k.md").exists())
        (self.pm / "k" / f"gesamt_{D}_k.md").unlink()
        v2 = self.pm / "k" / f"verdict_{D}_k_qwen36-35b_betrieb.md"
        v2.write_text("# Verdikt\n\n## Ergebnis\n\n**PASS** – ok\n", encoding="utf-8")
        code, out = self.rufen(kette.zusammenfuehren, [v, v2])
        self.assertTrue((self.pm / "k" / f"gesamt_{D}_k.md").is_file(), out)
        self.assertFalse((self.pm / f"gesamt_{D}_k.md").exists())


class UmsetzungImOrdner(Basis):

    def test_t4_umsetzung_auto_mit_ordner(self):
        """T4: umsetzung-auto – Prompt, Handover und Protokoll in der Ablage, Vorlagen bleiben"""
        (self.pm / "g").mkdir()
        for t in ("spec", "anforderung", "quellen"):
            self.git("mv", f"docs/projekt_management/{t}_{DATUM}_g.md", f"docs/projekt_management/g/{t}_{DATUM}_g.md")
        self.git("commit", "-qm", "Ablage g")
        neu = f"docs/projekt_management/g/handover_{DATUM}_g.md"
        code, out = self.lauf(FAKE_HANDOVER=neu)
        self.assertEqual(code, 0, out)
        self.assertTrue((self.pm / "g" / f"umsetzung_{DATUM}_g.md").is_file(), out)
        prompt = json.loads(self.argsdatei.read_text(encoding="utf-8"))[-1]
        self.assertIn(f"docs/projekt_management/g/spec_{DATUM}_g.md", prompt)
        self.assertIn(f"docs/projekt_management/g/handover_{DATUM}_g.md", prompt)
        self.assertNotIn(f"docs/projekt_management/spec_{DATUM}_g.md", prompt)
        self.assertNotIn("docs/projekt_management/g/_vorlage", prompt)
        self.assertNotIn("docs/projekt_management/g/g/", prompt)
        auftrag = self.pm / "g" / f"nacharbeit_{DATUM}_g_1.md"
        auftrag.write_text("Bitte X.\n", encoding="utf-8")
        nb = kette._umsetzung_prompt("g", DATUM, "abc", auftrag, 1)
        self.assertIn(f"Ergänze den Handover docs/projekt_management/g/handover_{DATUM}_g.md", nb)
        # Handover an der alten (flachen) Stelle gilt im Ordner-Fall nicht als geschrieben
        code, out = self.lauf(FAKE_HANDOVER=HANDOVER)
        self.assertNotEqual(code, 0, out)


class Kettendatei(Temp):

    def test_t5_kettendatei_im_ordner(self):
        """T5: _ist_kettendatei – Kettendateien im Ordner der Kette zählen"""
        (self.pm / "k").mkdir()
        self.assertTrue(kette._ist_kettendatei(f"docs/projekt_management/k/pruefung_{D}_k.md", "k"))
        self.assertTrue(kette._ist_kettendatei(f"docs/projekt_management/k/verdict_{D}_k_qwen36-35b.md", "k"))
        self.assertFalse(kette._ist_kettendatei(f"docs/projekt_management/k/spec_{D}_k.md", "k"))
        self.assertFalse(kette._ist_kettendatei(f"docs/projekt_management/x/pruefung_{D}_k.md", "k"))
        self.assertTrue(kette._ist_kettendatei(f"docs/projekt_management/pruefung_{D}_k.md", "k"))


class RollenProxy(Temp):

    def test_t6_role_proxy_spec_auftrag_im_ordner(self):
        """T6: role_proxy – Spec-Auftrag nennt Pfade in der Ablage"""
        from kette import _ablage_text
        self.assertEqual(_ablage_text("docs/projekt_management/spec_x.md docs/projekt_management/_vorlage_spec.md", "k"),
                         "docs/projekt_management/spec_x.md docs/projekt_management/_vorlage_spec.md")   # ohne Ordner
        (self.pm / "k").mkdir()
        self.assertEqual(_ablage_text("docs/projekt_management/spec_x.md docs/projekt_management/_vorlage_spec.md", "k"),
                         "docs/projekt_management/k/spec_x.md docs/projekt_management/_vorlage_spec.md")
        sys.path.insert(0, str(ECHT / "role-split"))
        self.addCleanup(sys.path.remove, str(ECHT / "role-split"))
        import role_proxy
        aus = io.StringIO()
        with redirect_stderr(aus):
            text = role_proxy.capture_task([{"role": "user", "content": "Neue Aufgabe k: Aufgabe Y"}])
        self.assertTrue(any((self.pm / "k").glob("anforderung_*_k.md")), aus.getvalue())
        self.assertRegex(text, r"docs/projekt_management/k/anforderung_\d{8}_k\.md")
        self.assertRegex(text, r"docs/projekt_management/k/spec_\d{8}_k\.md")
        self.assertNotIn("docs/projekt_management/k/k/", text)


class WeitereBefehle(Temp):

    def test_t7_pruefen_quellen_paket_prompt_in_der_ablage(self):
        """T7: pruefen, quellen, paket und prompt – Ausgaben und Pfade in der Ablage"""
        from unittest import mock
        o = self.pm / "k"
        o.mkdir()
        spec = ("# Spec: k\n\n## Ziel\nx\n\n## Quellen\n\n- `src/m.py` def f – Beispiel\n\n"
                "## Testplan\n\n### T1: Eins\n- **Erwartung:** x\n")
        (o / f"spec_{D}_k.md").write_text(spec, encoding="utf-8")
        (o / f"anforderung_{D}_k.md").write_text("# Anforderung: k\n\n## Aufgabe\n\n> X\n", encoding="utf-8")
        (self.root / "src").mkdir()
        (self.root / "src" / "m.py").write_text("def f():\n    return 1\n", encoding="utf-8")
        g = lambda *a: subprocess.run(["git", "-C", str(self.root), "-c", "user.name=t", "-c", "user.email=t@t", *a],
                                      check=True, capture_output=True, text=True).stdout
        g("init", "-q"); g("add", "."); g("commit", "-qm", "Spec k")
        commit = g("rev-parse", "--short", "HEAD").strip()
        code, out = self.rufen(kette.quellen, "k")
        self.assertTrue((o / f"quellen_{D}_k.md").is_file(), out)
        teile = {"abgleich": (0, "a"), "unittest": (0, "OK"), "gegenprobe": (0, "g")}
        with mock.patch.object(kette, "_pruefen_teile", lambda *a, **kw: teile):
            code, out = self.rufen(kette.pruefen, "k", commit)
        self.assertEqual(code, 0, out)
        self.assertTrue((o / f"pruefung_{D}_k.md").is_file(), out)
        (o / f"handover_{D}_k.md").write_text("# Handover k\n", encoding="utf-8")
        (self.root / "src" / "m.py").write_text("def f():\n    return 2\n", encoding="utf-8")
        code, out = self.rufen(kette.paket, "k", commit)
        self.assertTrue((o / f"review_paket_{D}_k.md").is_file(), out)
        self.assertFalse((self.pm / f"review_paket_{D}_k.md").exists())
        with mock.patch.object(kette.shutil, "which", return_value=None):
            code, out = self.rufen(kette.prompt, "umsetzung", "k", None, commit)
        self.assertIn(f"docs/projekt_management/k/spec_{D}_k.md", out)
        self.assertNotIn(f"docs/projekt_management/spec_{D}_k.md", out)
        with mock.patch.object(kette.shutil, "which", return_value=None):           # Nacharbeit 1: Platzhalter-Pfade
            code, out = self.rufen(kette.prompt, "review", "k", None, commit)
        self.assertIn(f"docs/projekt_management/k/verdict_{D}_k_<modellkürzel>.md", out)
        self.assertNotIn(f"docs/projekt_management/verdict_{D}_k_", out)


if __name__ == "__main__":
    unittest.main()
