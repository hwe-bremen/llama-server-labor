#!/usr/bin/env python3
"""Vorgabe-Tests fuer git_schutz (spec_20261101_git_schutz.md, T1–T8). Nicht aendern.

Keine Aussenwirkung: Jeder Lauf-Test baut ein eigenes temporaeres Git-Repo und biegt kette.ROOT/kette.PM
dorthin um. Statt opencode laeuft ein kleiner Wrapper (im Temp-Ordner geschrieben), der vorher Aktionen
im Temp-Repo ausfuehrt (git config, Hook schreiben, chmod, loeschen, Symlink) und dann die vorhandene
Attrappe role-split/kette/testdata/opencode_fake.py startet. Wrapper und Attrappe verweigern alles
ausserhalb des Temp-Ordners (technische Sperre). Jeder Test prueft zusaetzlich, dass HEAD, Arbeitsstand
und .git/config des echten Repos unveraendert bleiben. Neue Funktionen werden in den Methoden importiert.
"""
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

ECHT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ECHT / "role-split" / "kette"))
import kette  # noqa: E402

FAKE = ECHT / "role-split" / "kette" / "testdata" / "opencode_fake.py"
DATUM = "20261101"
HANDOVER = f"docs/projekt_management/handover_{DATUM}_g.md"
SPEC = (
    "# Spec: g\n\n## Ziel\nTest.\n\n## Schreibbereich\n\n- `src/`\n\n"
    "## Testplan\n\n### T1: Erster\n- **Erwartung:** x\n"
)

WRAPPER = '''import json, os, subprocess, sys, tempfile, runpy
def im_temp(p):
    t = os.path.realpath(tempfile.gettempdir())
    e = os.path.realpath(p)
    return e == t or e.startswith(t + os.sep)
d = sys.argv[sys.argv.index("--dir") + 1] if "--dir" in sys.argv else os.getcwd()
if not im_temp(d):
    print("wrapper: Sperre", file=sys.stderr)
    sys.exit(3)
for op, rel, arg in json.loads(os.environ.get("SCHUTZ_AKTIONEN") or "[]"):
    ziel = os.path.join(d, rel)
    if not im_temp(os.path.dirname(ziel) or d):
        print("wrapper: Sperre", file=sys.stderr)
        sys.exit(3)
    if op == "git":
        subprocess.run(["git", "-C", d, *arg], check=True)
    elif op == "anhaengen":
        os.makedirs(os.path.dirname(ziel), exist_ok=True)
        with open(ziel, "a", encoding="utf-8") as f:
            f.write(arg)
    elif op == "chmod":
        os.chmod(ziel, int(arg, 8))
    elif op == "loeschen":
        os.remove(ziel)
    elif op == "link":
        os.symlink(arg, ziel)
sys.argv = [FAKE] + sys.argv[1:]
runpy.run_path(FAKE, run_name="__main__")
'''


def _echter_stand() -> tuple:
    """HEAD, Status, Pruefsummen der offenen Dateien und von .git/config des echten Repos."""
    def g(*a):
        return subprocess.run(["git", "-C", str(ECHT), *a], capture_output=True, text=True).stdout
    summen = {}
    for eintrag in g("status", "--porcelain", "-z", "--untracked-files=all").split("\0"):
        pfad = ECHT / eintrag[3:] if len(eintrag) > 3 else None
        if pfad and pfad.is_file():
            summen[eintrag[3:]] = hashlib.sha256(pfad.read_bytes()).hexdigest()
    gd = g("rev-parse", "--git-common-dir").strip()
    cfg = (Path(gd) if os.path.isabs(gd) else ECHT / gd) / "config"
    cfg_summe = hashlib.sha256(cfg.read_bytes()).hexdigest() if cfg.is_file() else None
    return g("rev-parse", "HEAD").strip(), g("status", "--porcelain"), summen, cfg_summe


class Basis(unittest.TestCase):

    def setUp(self):
        self.echt_vorher = _echter_stand()
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        self.root = root = Path(d.name).resolve() / "repo"
        self.pm = root / "docs" / "projekt_management"
        self.pm.mkdir(parents=True)
        (self.pm / f"spec_{DATUM}_g.md").write_text(SPEC, encoding="utf-8")
        (self.pm / f"anforderung_{DATUM}_g.md").write_text("# Anforderung g\n", encoding="utf-8")
        (root / "src").mkdir()
        (root / "src" / "modul.py").write_text("X = 1\n", encoding="utf-8")
        (root / ".gitignore").write_text("role-split/results/\n", encoding="utf-8")
        self.git("init", "-q")
        self.gitdir = root / ".git"
        (self.gitdir / "hooks").mkdir(exist_ok=True)
        (self.gitdir / "hooks" / "pre-commit.sample").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        os.chmod(self.gitdir / "hooks" / "pre-commit.sample", 0o644)
        (self.gitdir / "hooks" / "pre-push.sample").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        (self.gitdir / "info").mkdir(exist_ok=True)
        (self.gitdir / "info" / "exclude").write_text("# exclude\n", encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", "Spec g")
        for name, wert in (("ROOT", root), ("PM", self.pm)):
            alt = getattr(kette, name)
            setattr(kette, name, wert)
            self.addCleanup(setattr, kette, name, alt)
        self.aufrufe_pruefen = 0

        def pruefen_attrappe(kurztitel, commit=None, timeout=300):
            self.aufrufe_pruefen += 1
            (self.pm / f"pruefung_{DATUM}_{kurztitel}.md").write_text(
                "# Pruefung\n\n## unittest  (Exit 0)\n\n```\nRan 1 test in 0.001s\n\nOK\n```\n", encoding="utf-8")
            return 0
        alt_pruefen = kette.pruefen
        kette.pruefen = pruefen_attrappe
        self.addCleanup(setattr, kette, "pruefen", alt_pruefen)
        wrapper = root.parent / "opencode_wrapper.py"
        wrapper.write_text(f"FAKE = {str(FAKE)!r}\n" + WRAPPER, encoding="utf-8")
        self.argsdatei = root.parent / "args.json"
        umgebung = {k: v for k, v in os.environ.items() if not k.startswith(("FAKE_", "SCHUTZ_"))}
        umgebung.update({"KETTE_OPENCODE": str(wrapper), "KETTE_UMSETZUNG_TIMEOUT": "60",
                         "FAKE_ARGS": str(self.argsdatei)})
        umgebung.pop("KETTE_UMSETZUNG_MODEL", None)
        p = mock.patch.dict(os.environ, umgebung, clear=True)
        p.start()
        self.addCleanup(p.stop)
        self.addCleanup(self._echt_unveraendert)

    def _echt_unveraendert(self):
        self.assertEqual(_echter_stand(), self.echt_vorher, "Test hat das echte Repo veraendert!")

    def git(self, *a) -> str:
        return subprocess.run(["git", "-C", str(self.root), "-c", "user.name=t", "-c", "user.email=t@t", *a],
                              check=True, capture_output=True, text=True).stdout

    def lauf(self, aktionen=(), nacharbeit=None, **fake):
        from kette import umsetzung_auto
        os.environ["SCHUTZ_AKTIONEN"] = json.dumps(list(aktionen))
        os.environ.update({k: str(v) for k, v in fake.items()})
        aus = io.StringIO()
        with redirect_stdout(aus), redirect_stderr(aus):
            code = umsetzung_auto("g", nacharbeit)
        return code, aus.getvalue()

    def protokoll(self) -> str:
        p = self.pm / f"umsetzung_{DATUM}_g.md"
        return p.read_text(encoding="utf-8") if p.exists() else ""

    def gestartet(self) -> bool:
        return self.argsdatei.exists()


class GitSchutzTests(Basis):

    def test_t1_unveraendertes_git_verzeichnis_lauf_ok(self):
        """T1: Unverändertes Git-Verzeichnis – Lauf OK, Zeile „Git-Schutz: unverändert“"""
        code, out = self.lauf(FAKE_EDIT="src/modul.py", FAKE_HANDOVER=HANDOVER)
        self.assertEqual(code, 0, out)
        self.assertIn("\nGit-Schutz: unverändert\n", out)
        self.assertNotIn("Git-Schutz verletzt", out)
        self.assertNotIn("git-schutz:", self.protokoll())
        self.assertIn("art: erst, Exit: 0", self.protokoll())
        self.assertEqual(self.aufrufe_pruefen, 1)

    def test_t2_git_config_user_name_test_fall_vom_27_10(self):
        """T2: git config user.name Test (Fall vom 27.10.) – lauter Befund, Exit 1, nichts zurückgesetzt"""
        code, out = self.lauf([["git", "", ["config", "user.name", "Test"]]], FAKE_HANDOVER=HANDOVER)
        self.assertEqual(code, 1, out)
        self.assertIn("!!! Git-Schutz verletzt – .git/ in diesem Lauf geändert (nichts zurückgesetzt):", out)
        self.assertIn("\n  .git/config (geaendert)", out)
        self.assertIn("\nGit-Schutz: geändert (1)\n", out)
        self.assertIn("art: erst, Exit: 1", self.protokoll())
        self.assertIn("\n  - git-schutz: .git/config (geaendert)\n", self.protokoll())
        self.assertEqual(self.git("config", "--local", "user.name").strip(), "Test")   # nichts zurueckgesetzt
        self.assertEqual(self.aufrufe_pruefen, 1)                                       # (c)/(d) laufen weiter
        self.assertNotIn("Schreibbereich verletzt", out)

    def test_t3_hooks_neu_ausfuehrbar_symlink_geloescht(self):
        """T3: hooks/ – neuer Hook, nur ausführbar gemacht, Symlink, gelöscht"""
        code, out = self.lauf([
            ["anhaengen", ".git/hooks/pre-commit", "#!/bin/sh\nexit 0\n"],
            ["chmod", ".git/hooks/pre-commit.sample", "755"],
            ["link", ".git/hooks/post-merge", "/gibt/es/nicht.sh"],
            ["loeschen", ".git/hooks/pre-push.sample", None],
        ], FAKE_HANDOVER=HANDOVER)
        self.assertEqual(code, 1, out)
        befund = out.split("!!! Git-Schutz verletzt", 1)[1].split("!!!", 1)[0]
        self.assertIn("  .git/hooks/pre-commit (neu)", befund)
        self.assertIn("  .git/hooks/pre-commit.sample (geaendert)", befund)
        self.assertIn("  .git/hooks/post-merge (neu)", befund)
        self.assertIn("  .git/hooks/pre-push.sample (weg)", befund)
        zeilen = [z for z in befund.splitlines() if z.startswith("  .git/")]
        self.assertEqual(zeilen, sorted(zeilen), "Einträge nicht sortiert")
        self.assertEqual(len(zeilen), 4, befund)
        self.assertIn("Git-Schutz: geändert (4)", out)
        self.assertEqual(self.protokoll().count("  - git-schutz: .git/hooks/"), 4)

    def test_t4_info_exclude_und_unterordner_auch_in_der_nacharbeit(self):
        """T4: info/ und Unterordner – auch im Nacharbeit-Lauf"""
        (self.root / HANDOVER).write_text("# Handover g\n", encoding="utf-8")
        auftrag = self.pm / f"nacharbeit_{DATUM}_g_1.md"
        auftrag.write_text("Bitte X.\n", encoding="utf-8")
        code, out = self.lauf([
            ["anhaengen", ".git/info/exclude", "src/\n"],
            ["anhaengen", ".git/hooks/tief/unten/hook", "x\n"],
        ], nacharbeit=str(auftrag), FAKE_HANDOVER=HANDOVER, FAKE_NACHBESSERUNG="1")
        self.assertEqual(code, 1, out)
        self.assertIn("  .git/info/exclude (geaendert)", out)
        self.assertIn("  .git/hooks/tief/unten/hook (neu)", out)
        self.assertIn("\nGit-Schutz: geändert (2)\n", out)
        self.assertIn("art: nb1, Exit: 1", self.protokoll())

    def test_t5_aenderungen_ausserhalb_der_geschuetzten_teile_kein_befund(self):
        """T5: Änderungen in .git/ außerhalb von config/hooks/info – kein Git-Schutz-Befund"""
        code, out = self.lauf([["anhaengen", ".git/description", "x\n"],
                               ["anhaengen", ".git/hooks_alt/notiz", "x\n"]], FAKE_HANDOVER=HANDOVER)
        self.assertEqual(code, 0, out)
        self.assertIn("\nGit-Schutz: unverändert\n", out)
        self.git("add", "-A")
        self.git("commit", "-qm", "zwischen")
        code, out = self.lauf(FAKE_HANDOVER=HANDOVER, FAKE_COMMIT="1")      # Selbst-Commit: logs/refs/index
        self.assertEqual(code, 1, out)
        self.assertIn("Selbst-Commit", out)
        self.assertNotIn("Git-Schutz verletzt", out)
        self.assertIn("\nGit-Schutz: unverändert\n", out)

    def test_t6_config_unlesbar_kein_absturz(self):
        """T6: config kaputt – kein Absturz, Befund, Protokollzeile, (c)/(d) übersprungen"""
        try:
            code, out = self.lauf([["anhaengen", ".git/config", "[kaputt\n"]], FAKE_HANDOVER=HANDOVER)
        except subprocess.CalledProcessError as e:
            self.fail(f"Absturz statt Befund: {e}")
        self.assertEqual(code, 1, out)
        self.assertIn("  .git/config (geaendert)", out)
        self.assertIn("!!! git nach dem Lauf nicht benutzbar (git rev-parse HEAD: ", out)
        self.assertIn("(c) übersprungen (git nicht benutzbar)", out)
        self.assertEqual(self.aufrufe_pruefen, 0)
        self.assertNotIn("Selbst-Commit", out)
        self.assertIn("  - git-schutz: .git/config (geaendert)", self.protokoll())
        self.assertIn("rot: –, pruefen: –, art: erst, Exit: 1", self.protokoll())

    def test_t7_git_verzeichnis_worktree_und_fehlt(self):
        """T7: Git-Verzeichnis – Worktree nutzt das des Hauptrepos; nicht bestimmbar → Exit 2, kein Start"""
        from kette import _git_verzeichnis
        self.assertEqual(_git_verzeichnis(), self.gitdir.resolve())
        baum = self.root.parent / "baum"
        self.git("worktree", "add", "-q", str(baum))
        with mock.patch.object(kette, "ROOT", baum):
            self.assertEqual(_git_verzeichnis(), self.gitdir.resolve())
        self.git("worktree", "remove", "--force", str(baum))
        with mock.patch.object(kette, "ROOT", self.root.parent):     # kein Repo
            self.assertIsNone(_git_verzeichnis())
        with mock.patch.object(kette, "_git_verzeichnis", return_value=None):
            code, out = self.lauf(FAKE_HANDOVER=HANDOVER)
        self.assertEqual(code, 2, out)
        self.assertIn("Git-Verzeichnis", out)
        self.assertFalse(self.gestartet())

    def test_t8_standardwerte_im_echten_pfad(self):
        """T8: Standardwerte im echten Pfad – GIT_SCHUTZ, echtes Git-Verzeichnis, nur lesend"""
        from kette import GIT_SCHUTZ, _git_schutz, _git_verzeichnis
        self.assertEqual(GIT_SCHUTZ, ("config", "hooks", "info"))
        with mock.patch.object(kette, "ROOT", ECHT):
            echt = _git_verzeichnis()
        erwartet = subprocess.run(["git", "-C", str(ECHT), "rev-parse", "--path-format=absolute",
                                   "--git-common-dir"], capture_output=True, text=True).stdout.strip()
        self.assertEqual(echt, Path(erwartet).resolve())
        stand = _git_schutz(echt)
        self.assertIn("config", stand)
        self.assertTrue(all(k == "config" or k.startswith(("hooks/", "info/")) for k in stand), stand)
        self.assertRegex(stand["config"], r"^[0-9a-f]{64}$")
        self.assertEqual(_git_schutz(echt), stand)                     # nur lesend, stabil


if __name__ == "__main__":
    unittest.main()
