#!/usr/bin/env python3
"""Selbsttest des Prüfers: Musterlösung muss volle Punkte holen, gezielt verfälschte Varianten
müssen genau die erwarteten Punkte verlieren (Gegenproben).

    .venv/bin/python -m unittest -v experiments/slipstream_20261017/wissensbreite_gguf/selbsttest/test_pruefen.py
Braucht gguf-py + numpy (wie pruefen.py) und erzeugt die synthetischen Dateien bei Bedarf.
"""
import sys
import tempfile
import unittest
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parent))
import pruefen  # noqa: E402

MUSTER = (HIER / "muster_gguf_lesen.py").read_text(encoding="utf-8")
D1 = pruefen.PRUEFDATEIEN / "synth_klassisch.gguf"


def variante(alt: str, neu: str) -> str:
    assert MUSTER.count(alt) == 1, alt
    return MUSTER.replace(alt, neu)


class PrueferTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not D1.exists():
            pruefen.cmd_synth(None)
        cls.tmp = tempfile.TemporaryDirectory()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def bewerte(self, code: str, name: str, trotzdem=False):
        lauf = Path(self.tmp.name) / name
        lauf.mkdir()
        (lauf / "gguf_lesen.py").write_text(code, encoding="utf-8")
        return pruefen.lauf_bewerten(lauf, [D1], trotzdem)

    def punkte(self, erg):
        return {k for k, v in erg["dateien"][D1.name]["punkte"].items() if v}

    def test_01_muster_volle_punkte(self):
        erg = self.bewerte(MUSTER, "muster")
        self.assertEqual(erg["summe"], 8, erg)

    def test_02_default_alignment_ignoriert(self):
        code = variante('align = meta.get("general.alignment", {}).get("value", 32)', "align = 32")
        p = self.punkte(self.bewerte(code, "align32"))
        self.assertNotIn("alignment_offset", p)
        self.assertNotIn("ende", p)
        self.assertIn("n_bytes", p)
        self.assertIn("tensor_infos", p)

    def test_03_q6k_falsch(self):
        code = variante('14: ("Q6_K", 256, 210)', '14: ("Q6_K", 256, 208)')
        erg = self.bewerte(code, "q6k")
        p = self.punkte(erg)
        self.assertNotIn("n_bytes", p)
        self.assertIn("alignment_offset", p)
        self.assertIn("Q6_K", str(erg["dateien"][D1.name]["info"]["n_bytes"]))

    def test_04_typname_falsch(self):
        code = variante('30: ("BF16", 1, 2)', '30: ("BFLOAT16", 1, 2)')
        self.assertNotIn("n_bytes", self.punkte(self.bewerte(code, "bfname")))

    def test_05_typ_unbekannt_kein_absturz(self):
        code = variante('23: ("IQ4_XS", 256, 136), ', '')
        erg = self.bewerte(code, "unbekannt")
        p = self.punkte(erg)
        self.assertNotIn("n_bytes", p)
        self.assertIn("tensor_infos", p)

    def test_06_bool_als_int(self):
        code = variante('7: "<?"', '7: "<B"')
        p = self.punkte(self.bewerte(code, "boolint"))
        self.assertNotIn("meta_skalare", p)
        self.assertNotIn("meta_arrays", p)
        self.assertIn("meta_typen", p)

    def test_07_numpy_disqualifiziert(self):
        erg = self.bewerte("import numpy\n" + MUSTER, "numpy")
        self.assertTrue(erg["status"].startswith("DISQUALIFIZIERT"), erg["status"])
        self.assertEqual(erg["summe"], 0)

    def test_08_riskant_nicht_ausgefuehrt(self):
        code = MUSTER.replace("import json\n", "import json\nimport os\nos.system('true')\n", 1)
        erg = self.bewerte(code, "riskant")
        self.assertTrue(erg["status"].startswith("NICHT AUSGEFÜHRT"), erg["status"])
        self.assertEqual(erg["dateien"], {})

    def test_09_harmlose_methoden_nicht_riskant(self):
        code = MUSTER.replace("import json\n", "import json\nimport re\nRE = re.compile('x')\n_l = [1]; _l.remove(1)\n"
                              "_s = 'a'.replace('a', 'b')\n", 1)
        erg = self.bewerte(code, "harmlos")
        self.assertEqual(erg["code"]["riskant"], [])
        self.assertEqual(erg["summe"], 8)

    def test_10_zusatztext_kein_json(self):
        code = MUSTER.replace("    main(sys.argv[1])", "    print('Ergebnis:')\n    main(sys.argv[1])")
        erg = self.bewerte(code, "text")
        self.assertIn("kein gültiges JSON", erg["dateien"][D1.name]["fehler"])

    def test_14_relativer_pfad(self):
        """Laufordner relativ zum aktuellen Verzeichnis angegeben (Befund Selbsttest 20.10.)."""
        import os
        lauf = Path(self.tmp.name) / "relativ"
        lauf.mkdir()
        (lauf / "gguf_lesen.py").write_text(MUSTER, encoding="utf-8")
        alt = os.getcwd()
        os.chdir(self.tmp.name)
        try:
            erg = pruefen.lauf_bewerten(Path("relativ"), [D1], False)
        finally:
            os.chdir(alt)
        self.assertEqual(erg["summe"], 8, erg)

    def test_15_fehler_auf_stdout_sichtbar(self):
        """Leser, die Fehler als JSON auf stdout melden und mit 1 enden (Qwen3-Next 20.10.)."""
        code = "import json, sys\nprint(json.dumps({'error': 'kaputt'}))\nsys.exit(1)\n"
        erg = self.bewerte(code, "stdoutfehler")
        self.assertIn("kaputt", erg["dateien"][D1.name]["fehler"])

    def test_11_zeitgrenze(self):
        lauf = Path(self.tmp.name) / "langsam"
        lauf.mkdir()
        (lauf / "gguf_lesen.py").write_text("import time\ntime.sleep(5)\n", encoding="utf-8")
        e = pruefen.kandidat_ausfuehren(lauf / "gguf_lesen.py", D1, zeitgrenze=1)
        self.assertIn("Zeitüberschreitung", e["fehler"])

    def test_12_metadaten_mit_kopfzaehlern(self):
        code = variante("        meta = {}\n", '        meta = {"GGUF.version": {"type_id": 4, "value": 3}}\n')
        p = self.punkte(self.bewerte(code, "kopfmeta"))
        self.assertNotIn("meta_typen", p)

    def test_13_schluessel_tabelle_wie_gguf_py(self):
        """Die Blockgrößen der Musterlösung (und damit der Schlüssel) entsprechen gguf-py."""
        _, _, Q, _, sizes = pruefen.lade_gguf()
        ns = {}
        exec(compile(MUSTER.split("class Leser")[0], "muster", "exec"), ns)
        for tid, (name, bs, ts) in ns["GGML"].items():
            self.assertEqual(Q(tid).name, name)
            self.assertEqual(tuple(sizes[Q(tid)]), (bs, ts), name)


if __name__ == "__main__":
    unittest.main()
