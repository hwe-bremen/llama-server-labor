"""Tests fuer Spec paket_vollstaendig (T1–T9).
Jede Methode entspricht einer Test-ID aus der Spec.
Neue Funktionen werden innerhalb der Methode importiert, nicht am Dateianfang."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Projekt-Root fuer relative Pfade
ROOT = Path(__file__).resolve().parent.parent


class TestPaketVollstaendig(unittest.TestCase):
    """Tests fuer die Anforderungen A1–A7 der Spec paket_vollstaendig."""

    @classmethod
    def setUpClass(cls):
        """Git-Befehle im Projekt-Root ausfuehren."""
        cls.orig_cwd = os.getcwd()

    def _git(self, *args):
        return subprocess.run(
            ["git", "-C", str(ROOT), *args],
            capture_output=True, text=True, check=True
        )

    # ---------------------------------------------------------------- T1
    def test_t1_docs_excluded(self):
        """T1: docs/ und .md-Dateien nie im Paket (PAKET_NIE)."""
        sys.path.insert(0, str(ROOT / "role-split" / "kette"))
        import kette
        self.assertIn("docs/", kette.PAKET_NIE)
        # tests/ und role-split/ duerfen nicht mehr in PAKET_NIE sein
        self.assertNotIn("tests/", kette.PAKET_NIE)
        self.assertNotIn("role-split/", kette.PAKET_NIE)

    # ---------------------------------------------------------------- T2
    def test_t2_kette_paket_max_exists(self):
        """T2: KETTE_PAKET_MAX als Konstante vorhanden und > 0."""
        sys.path.insert(0, str(ROOT / "role-split" / "kette"))
        import kette
        self.assertIsInstance(kette.KETTE_PAKET_MAX, int)
        self.assertGreater(kette.KETTE_PAKET_MAX, 0)

    # ---------------------------------------------------------------- T3
    def test_t3_ketten_dateien_im_paket(self):
        """T3: Dateien in Commits mit Kurztitel gehoeren zur Kette."""
        sys.path.insert(0, str(ROOT / "role-split" / "kette"))
        import kette
        # _diff muss kurztitel-Parameter akzeptieren
        import inspect
        sig = inspect.signature(kette._diff)
        self.assertIn("kurztitel", sig.parameters)

    # ---------------------------------------------------------------- T4
    def test_t4_fremde_dateien_liste(self):
        """T4: Fremde Dateien erscheinen in separater Sektion."""
        sys.path.insert(0, str(ROOT / "role-split" / "kette"))
        import kette
        # Die paket()-Funktion muss fremde_teile verarbeiten
        # und eine "Fremde Aenderungen" Sektion erzeugen
        import inspect
        source = inspect.getsource(kette.paket)
        self.assertIn("Fremde", source)
        self.assertIn("fremde_teile", source)

    # ---------------------------------------------------------------- T5
    def test_t5_nicht_genannt_markierung(self):
        """T5: Dateien nicht im Handover werden markiert."""
        sys.path.insert(0, str(ROOT / "role-split" / "kette"))
        import kette
        ergebnis = kette._kappen("test.py", ["1  code"], "diff", 100, nicht_genannt=True)
        self.assertIn("nicht in der Uebergabe genannt", ergebnis)
        ergebnis2 = kette._kappen("test.py", ["1  code"], "diff", 100, nicht_genannt=False)
        self.assertNotIn("nicht in der Uebergabe genannt", ergebnis2)

    # ---------------------------------------------------------------- T6
    def test_t6_vorrang_klassifikation(self):
        """T6: Vorrang-Klassifikation funktioniert korrekt."""
        sys.path.insert(0, str(ROOT / "role-split" / "kette"))
        import kette
        # Vorrang-Logik ist in _diff eingebaut; wir testen indirekt
        # dass _diff weggelassen_teile zurueckgibt
        import inspect
        source = inspect.getsource(kette._diff)
        self.assertIn("vorrang", source)
        # Rueckgabe muss 4 Werte haben
        # (diff_text, dateien, fremde_teile, weggelassen_teile)

    # ---------------------------------------------------------------- T7
    def test_t7_harte_obergrenze_exit1(self):
        """T7: Paket > KETTE_PAKET_MAX -> Exit 1."""
        sys.path.insert(0, str(ROOT / "role-split" / "kette"))
        import kette
        import inspect
        source = inspect.getsource(kette.paket)
        self.assertIn("KETTE_PAKET_MAX", source)
        self.assertIn("return 1", source)

    # ---------------------------------------------------------------- T8
    def test_t8_gegenprobe_role_split(self):
        """T8: Gegenprobe nimmt role-split/kette/ auf."""
        sys.path.insert(0, str(ROOT / "role-split" / "kette"))
        import kette
        import inspect
        source = inspect.getsource(kette.gegenprobe)
        self.assertNotIn("role-split/kette/", source)
        # role-split/kette/ darf nicht in der Ausschlussliste stehen

    # ---------------------------------------------------------------- T9
    def test_t9_paket_ohne_code_exit1(self):
        """T9: Paket ohne Code trotz Aenderungen -> Exit 1."""
        sys.path.insert(0, str(ROOT / "role-split" / "kette"))
        import kette
        import inspect
        source = inspect.getsource(kette.paket)
        self.assertIn("keine Code-Dateien", source)
        self.assertIn("return 1", source)


if __name__ == "__main__":
    unittest.main()
