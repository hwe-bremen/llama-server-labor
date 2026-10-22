#!/usr/bin/env python3
"""
Tests fuer spec_20261021_search_results_verbessern (A1-A6, T1-T12).

Alle Tests als unittest, ohne Außenwirkung.
Neue Funktionen werden innerhalb der Testmethode importiert.
"""

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import textwrap
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

# Pfad zum Repo-Root (zwei Verzeichnisse aufwaerts von tests/)
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCOUT_DIR = _REPO_ROOT / "agents" / "llm_scout"
_SCOUT_SCRIPT = _SCOUT_DIR / "llm_scout.py"


class TestSearchResultsVerbessern(unittest.TestCase):
    """Tests T1-T12 fuer search_results_verbessern."""

    @staticmethod
    def _run_main(tmp_dir: Path, sources_json: dict,
                  hf_fetched: int = 0, hf_items: list = None,
                  gh_fetched_items: dict = None,
                  llm_response: str = "# LLM Scout Weekly\n\n## Hugging Face (neue Modelle)\n\nKeine neuen Modelle in den letzten 7 Tagen.\n\n## GitHub: ggml-org/llama.cpp\n\nKeine neuen Releases in den letzten 7 Tagen.\n\n## GitHub: ollama/ollama\n\nKeine neuen Releases in den letzten 7 Tagen.\n\n## Slipstream neueste Entwicklungen\n\nKeine neuen Entwicklungen in den letzten 7 Tagen.\n\n## Fazit\n\nNichts Neues.",
                  db_path: Path = None) -> tuple:
        """
        Fuehrt main() aus mit gemockten Abhaengigkeiten.

        Returns:
            (exit_code, report_path, stderr_text)
        """
        import io
        from agents.llm_scout import llm_scout

        if hf_items is None:
            hf_items = []
        if gh_fetched_items is None:
            gh_fetched_items = {}

        sources_path = tmp_dir / "sources.json"
        sources_path.write_text(json.dumps(sources_json))

        report_dir = tmp_dir / "weekly-reports"
        report_dir.mkdir(parents=True, exist_ok=True)

        db = db_path or (tmp_dir / "test.db")

        stderr_capture = io.StringIO()

        def mock_fetch_hf():
            return (hf_fetched, list(hf_items))

        def mock_fetch_github(rss_url, repo_name):
            source_key = llm_scout.get_source_key_for_repo(repo_name)
            result = gh_fetched_items.get(source_key, (0, []))
            return (result[0], list(result[1]))

        def mock_call_llm(items, sources_config):
            return llm_response

        def mock_router_ready(timeout=5.0):
            return True

        # Patch module-level Konstanten und Funktionen
        with patch.object(llm_scout, '_SOURCES_JSON_PATH', sources_path), \
             patch.object(llm_scout, 'DB_PATH', db), \
             patch.object(llm_scout, 'BASE_DIR', tmp_dir), \
             patch.object(llm_scout, 'REPORT_DIR', report_dir), \
             patch.object(llm_scout, 'fetch_hf_trending', mock_fetch_hf), \
             patch.object(llm_scout, 'fetch_github_releases_for_repo', mock_fetch_github), \
             patch.object(llm_scout, 'call_llm_for_evaluation', mock_call_llm), \
             patch.object(llm_scout, 'router_ready', mock_router_ready), \
             patch("sys.stderr", stderr_capture):

            exit_code = 0
            try:
                llm_scout.main()
            except SystemExit as e:
                exit_code = e.code if e.code is not None else 0

            # Berichtspfad ermitteln
            iso_year, iso_week, _ = datetime.now().isocalendar()
            report_filename = f"llm_scout_kw{iso_week}_{iso_year}.md"
            report_path = report_dir / report_filename

            return (exit_code, report_path, stderr_capture.getvalue())

    # ======================== T1 ========================
    def test_t1_feed_404_prookol_zeigt_fetched_0(self):
        """T1: Feed-Fehler (404) -> Quelle im Protokoll mit fetched: 0, Scout bricht nicht ab."""
        from agents.llm_scout.llm_scout import (
            fetch_github_releases_for_repo,
            fetch_hf_trending,
            write_source_run_log,
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            lab_dir = Path(tmp_dir)
            sources_path = lab_dir / "sources.json"
            sources_path.write_text(json.dumps({
                "github": [
                    {"repo": "ggml-org/llama.cpp", "rss": "https://github.com/ggml-org/llama.cpp/releases.atom"},
                    {"repo": "bad/repo404", "rss": "https://github.com/bad/repo404/releases.atom"},
                ]
            }))

            # Mock: guter Feed fuer llama.cpp, 404 fuer bad/repo404
            def mock_get(url, **kwargs):
                if "repo404" in url:
                    resp = MagicMock()
                    resp.status_code = 404
                    resp.raise_for_status.side_effect = Exception("404 Not Found")
                    return resp
                else:
                    # Gueltiger Feed-Inhalt (minimal)
                    resp = MagicMock()
                    resp.status_code = 200
                    resp.content = b"""<?xml version="1.0"?>
                    <feed xmlns="http://www.w3.org/2005/Atom">
                      <entry>
                        <title>Release b100</title>
                        <link>https://github.com/ggml-org/llama.cpp/releases/tag/b100</link>
                        <summary>Test release</summary>
                        <updated>2026-10-21T12:00:00Z</updated>
                      </entry>
                    </feed>"""
                    return resp

            with patch("requests.get", side_effect=mock_get):
                hf_fetched, hf_items = fetch_hf_trending()
                llama_fetched, items_llama = fetch_github_releases_for_repo(
                    "https://github.com/ggml-org/llama.cpp/releases.atom",
                    "ggml-org/llama.cpp"
                )
                fetched_404, items_404 = fetch_github_releases_for_repo(
                    "https://github.com/bad/repo404/releases.atom",
                    "bad/repo404"
                )

            # Protokoll bauen und schreiben (mit neuer 'new'-Stufe)
            source_data = {
                "huggingface": {
                    "fetched": hf_fetched,
                    "after_filter": len(hf_items),
                    "new": len(hf_items),
                    "sent_to_llm": [{"url": i["url"], "title": i["title"]} for i in hf_items]
                },
                "github:ggml-org/llama.cpp": {
                    "fetched": llama_fetched,
                    "after_filter": len(items_llama),
                    "new": len(items_llama),
                    "sent_to_llm": [{"url": i["url"], "title": i["title"]} for i in items_llama]
                },
                "github:bad/repo404": {
                    "fetched": fetched_404,
                    "after_filter": len(items_404),
                    "new": len(items_404),
                    "sent_to_llm": []
                }
            }
            write_source_run_log(lab_dir, source_data)

            # Protokoll-Datei muss existieren
            log_files = list(lab_dir.glob("source_run_log_*.jsonl"))
            self.assertEqual(len(log_files), 1, "Protokoll-Datei existiert nicht")

            # 404-Quelle hat fetched: 0
            with open(log_files[0], 'r') as f:
                log_line = json.loads(f.readline())
            self.assertEqual(log_line["github:bad/repo404"]["fetched"], 0,
                             "404-Quelle sollte fetched: 0 haben")

    # ======================== T2 ========================
    def test_t2_sources_json_fehlt_exit_1(self):
        """T2: sources.json fehlt -> Exit 1, keine DB-Aenderung."""
        from agents.llm_scout.llm_scout import load_sources
        import io

        with tempfile.TemporaryDirectory() as tmp_dir:
            lab_dir = Path(tmp_dir)
            # sources.json existiert nicht im tmp_dir
            missing_path = lab_dir / "sources.json"

            # load_sources mit nicht-existentem Pfad -> SystemExit(1)
            stderr_io = io.StringIO()
            with self.assertRaises(SystemExit) as ctx:
                with patch("sys.stderr", stderr_io):
                    load_sources(missing_path)

            self.assertEqual(ctx.exception.code, 1,
                             f"Exit-Code sollte 1 sein, ist {ctx.exception.code}")
            stderr_output = stderr_io.getvalue()
            self.assertIn("sources.json nicht gefunden", stderr_output,
                          f"stderr sollte 'sources.json nicht gefunden' enthalten: {stderr_output}")
            # Keine DB im tmp_dir
            db_path = lab_dir / "llm_scout.db"
            self.assertFalse(db_path.exists(), "DB sollte nicht angelegt werden")
            # Kein Protokoll
            log_files = list(lab_dir.glob("source_run_log_*.jsonl"))
            self.assertEqual(len(log_files), 0, "Kein Protokoll darf geschrieben werden")

    # ======================== T3 ========================
    def test_t3_unbekannter_key_warnung(self):
        """T3: sources.json mit unbekanntem Key -> Warnung, Exit 0, nur erkannte Quellen."""
        import io
        from agents.llm_scout.llm_scout import load_sources

        with tempfile.TemporaryDirectory() as tmp_dir:
            lab_dir = Path(tmp_dir)
            sources_path = lab_dir / "sources.json"
            sources_path.write_text(json.dumps({
                "github": [
                    {"repo": "ggml-org/llama.cpp", "rss": "https://github.com/ggml-org/llama.cpp/releases.atom"}
                ],
                "gitlab": [
                    {"repo": "test/gitlab", "rss": "https://gitlab.com/test/gitlab/releases.atom"}
                ]
            }))

            stderr_io = io.StringIO()
            with patch("sys.stderr", stderr_io):
                sources = load_sources(sources_path)

            self.assertIn("github", sources, "github-Key muss erkannt werden")
            self.assertNotIn("gitlab", sources, "gitlab-Key muss ignoriert werden")

            # Warnung auf stderr
            stderr_output = stderr_io.getvalue()
            self.assertIn("gitlab", stderr_output.lower(),
                          f"Warnung sollte 'gitlab' erwahnen: {stderr_output}")

    # ======================== T4 ========================
    def test_t4_slipstream_filter_nur_schero94(self):
        """T4: Slipstream-Filter - nur Schero94/slipstream, kein anderes slipstream-Projekt."""
        from agents.llm_scout.llm_scout import (
            get_source_key_for_repo,
            fetch_github_releases_for_repo,
            SLIPSTREAM_REPO,
        )

        # Source-Key-Zuordnung
        self.assertEqual(get_source_key_for_repo("Schero94/slipstream"), "slipstream",
                          "Schero94/slipstream muss 'slipstream' ergeben")
        self.assertEqual(get_source_key_for_repo("chenzhuofu/slipstream"),
                          "github:chenzhuofu/slipstream",
                          "chenzhuofu/slipstream darf nicht 'slipstream' ergeben")
        self.assertEqual(get_source_key_for_repo("ggml-org/llama.cpp"),
                          "github:ggml-org/llama.cpp")

        # Mock-Feed mit einem Entry
        mock_content = b"""<?xml version="1.0"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
          <entry>
            <title>Slipstream v0.1</title>
            <link>https://github.com/Schero94/slipstream/releases/tag/v0.1</link>
            <summary>Test</summary>
            <updated>2026-10-21T12:00:00Z</updated>
          </entry>
        </feed>"""

        def mock_get(url, **kwargs):
            resp = MagicMock()
            resp.status_code = 200
            resp.content = mock_content
            return resp

        with patch("requests.get", side_effect=mock_get):
            _, slip_items = fetch_github_releases_for_repo(
                "https://github.com/Schero94/slipstream/releases.atom",
                "Schero94/slipstream"
            )
            _, chenzhuo_items = fetch_github_releases_for_repo(
                "https://github.com/chenzhuofu/slipstream/releases.atom",
                "chenzhuofu/slipstream"
            )

        # Slipstream-Items haben source='slipstream'
        for item in slip_items:
            self.assertEqual(item["source"], "slipstream",
                              f"Schero94/slipstream-Item muss source='slipstream' haben, ist '{item['source']}'")

        # chenzhuofu-Items haben source='github:chenzhuofu/slipstream'
        for item in chenzhuo_items:
            self.assertEqual(item["source"], "github:chenzhuofu/slipstream",
                              f"chenzhuofu-Item muss source='github:chenzhuofu/slipstream' haben, ist '{item['source']}'")

        # Kein chenzhuofu-Item in slipstream-Liste
        self.assertNotIn("github:chenzhuofu/slipstream",
                          [i["source"] for i in slip_items],
                          "chenzhuofu-Item darf nicht in slipstream-Liste sein")

    # ======================== T5 ========================
    def test_t5_select_items_pro_quelle_top3(self):
        """T5: select_items() pro Quelle - Top 3, leere Quelle bleibt sichtbar."""
        from agents.llm_scout.llm_scout import select_items, ITEMS_PER_SOURCE

        # 10 Items fuer repo_a, 0 fuer repo_b
        items_a = [{"source": "github:repo_a", "title": f"Item {i}", "url": f"http://a/{i}", "summary": "s"}
                   for i in range(10)]
        items_b = []  # leere Quelle
        all_items = items_a + items_b

        selected = select_items(all_items)

        # Pro Quelle max ITEMS_PER_SOURCE
        selected_a = [i for i in selected if i["source"] == "github:repo_a"]
        selected_b = [i for i in selected if i["source"] == "github:repo_b"]

        self.assertEqual(len(selected_a), ITEMS_PER_SOURCE,
                         f"repo_a sollte {ITEMS_PER_SOURCE} Items haben, hat {len(selected_a)}")
        self.assertEqual(len(selected_b), 0,
                         "repo_b sollte 0 Items haben")

    # ======================== T6 ========================
    def test_t6_db_source_wert_korrekt(self):
        """T6: DB source-Wert korrekt befuellt, UNIQUE-Constraint respektiert."""
        from agents.llm_scout.llm_scout import assign_source_tags, mark_as_processed, init_db

        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "test.db"
            conn = sqlite3.connect(str(db_path))
            init_db(conn)

            # (a) slipstream
            item_a = {"title": "Slipstream v0.1", "url": "https://github.com/Schero94/slipstream/releases/tag/v0.1"}
            tagged_a = assign_source_tags(item_a, "slipstream")
            mark_as_processed(conn, tagged_a["source"], tagged_a["title"], tagged_a["url"])

            cursor = conn.execute("SELECT source FROM processed_items WHERE url=?", (tagged_a["url"],))
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], "slipstream",
                             f"source sollte 'slipstream' sein, ist '{row[0]}'")

            # (b) llama.cpp
            item_b = {"title": "b100", "url": "https://github.com/ggml-org/llama.cpp/releases/tag/b100"}
            tagged_b = assign_source_tags(item_b, "github:ggml-org/llama.cpp")
            mark_as_processed(conn, tagged_b["source"], tagged_b["title"], tagged_b["url"])

            cursor = conn.execute("SELECT source FROM processed_items WHERE url=?", (tagged_b["url"],))
            row = cursor.fetchone()
            self.assertEqual(row[0], "github:ggml-org/llama.cpp")

            # (c) Doppelte Markierung mit anderem source-Wert -> UNIQUE-Constraint
            mark_as_processed(conn, "slipstream", "b100", tagged_b["url"])

            cursor = conn.execute("SELECT source FROM processed_items WHERE url=?", (tagged_b["url"],))
            row = cursor.fetchone()
            self.assertEqual(row[0], "github:ggml-org/llama.cpp",
                             "Doppelte Markierung sollte originalen source-Wert erhalten lassen")

            cursor = conn.execute("SELECT COUNT(*) FROM processed_items WHERE url=?", (tagged_b["url"],))
            count = cursor.fetchone()[0]
            self.assertEqual(count, 1, "Doppelte URL darf nur einen Eintrag haben")

            conn.close()

    # ======================== T7 ========================
    def test_t7_llm_fehler_kein_bericht_protokoll_existiert(self):
        """T7: LLM-Fehler -> kein Bericht, Protokoll existiert, Exit 1."""
        from agents.llm_scout.llm_scout import call_llm_for_evaluation, write_source_run_log

        with tempfile.TemporaryDirectory() as tmp_dir:
            lab_dir = Path(tmp_dir)
            report_dir = lab_dir / "weekly-reports"
            report_dir.mkdir()

            # Protokoll schreiben (vor LLM-Aufruf)
            source_data = {
                "huggingface": {"fetched": 0, "after_filter": 0, "new": 0, "sent_to_llm": []},
                "slipstream": {"fetched": 0, "after_filter": 0, "new": 0, "sent_to_llm": []}
            }
            write_source_run_log(lab_dir, source_data)

            # LLM-Aufruf mocken: requests.post liefert leeren content -> RuntimeError
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "choices": [{"message": {"content": ""}}]
            }
            mock_resp.raise_for_status.return_value = None

            # sources_config mit mindestens einer Quelle (erforderlich fuer build_prompt_sections)
            sources_config = {"github": []}

            with patch("requests.post", return_value=mock_resp):
                with self.assertRaises(RuntimeError) as ctx:
                    call_llm_for_evaluation([], sources_config)

            self.assertIn("leeren Inhalt", str(ctx.exception))

            # Protokoll existiert
            log_files = list(lab_dir.glob("source_run_log_*.jsonl"))
            self.assertEqual(len(log_files), 1, "Protokoll muss existieren")

            # Kein Bericht
            report_files = list(report_dir.glob("*.md"))
            self.assertEqual(len(report_files), 0, "Kein Bericht darf geschrieben werden")

    # ======================== T8 ========================
    def test_t8_leere_sources_bericht_mit_hf_und_slipstream(self):
        """T8: leere sources.json {} -> Exit 0, Bericht mit Hugging-Face- und Slipstream-Sektion (via main())."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            # LLM-Antwort ohne Sektionen (secure_report_sections muss sie nachtragen)
            llm_response = "# LLM Scout Weekly\n\n## Fazit\n\nNichts Neues."

            exit_code, report_path, stderr_text = self._run_main(
                tmp_path,
                sources_json={},
                llm_response=llm_response
            )

            self.assertEqual(exit_code, 0, f"Exit-Code sollte 0 sein, ist {exit_code}")
            self.assertTrue(report_path.exists(), "Bericht muss existieren")

            content = report_path.read_text()
            self.assertIn("## Hugging Face (neue Modelle)", content,
                          "Bericht muss Hugging-Face-Sektion enthalten")
            self.assertIn("## Slipstream neueste Entwicklungen", content,
                          "Bericht muss Slipstream-Sektion enthalten")
            # Slipstream ist nicht konfiguriert -> "nicht konfiguriert"
            self.assertIn("nicht konfiguriert", content,
                          "Slipstream muss als 'nicht konfiguriert' markiert sein")

    # ======================== T9b (neu) ========================
    def test_t9b_alte_eintraege_kein_bericht_alle_sektionen(self):
        """Neuer Test: alle Feeds nur mit alten Eintraegen, noch kein Wochenbericht -> Bericht mit allen Sektionen (via main())."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            sources_json = {
                "github": [
                    {"repo": "ggml-org/llama.cpp", "rss": "https://github.com/ggml-org/llama.cpp/releases.atom"},
                    {"repo": "ollama/ollama", "rss": "https://github.com/ollama/ollama/releases.atom"},
                ]
            }
            # LLM-Antwort mit allen Sektionen (da keine neuen Items, aber erster Lauf)
            llm_response = "# LLM Scout Weekly\n\n## Fazit\n\nNichts Neues."

            exit_code, report_path, stderr_text = self._run_main(
                tmp_path,
                sources_json=sources_json,
                hf_fetched=5,
                hf_items=[],  # keine neuen HF-Items
                gh_fetched_items={
                    "github:ggml-org/llama.cpp": (3, []),
                    "github:ollama/ollama": (2, []),
                },
                llm_response=llm_response
            )

            self.assertEqual(exit_code, 0, f"Exit-Code sollte 0 sein, ist {exit_code}")
            self.assertTrue(report_path.exists(), "Bericht muss existieren (erster Lauf der Woche)")

            content = report_path.read_text()
            self.assertIn("## Hugging Face (neue Modelle)", content,
                          "Bericht muss Hugging-Face-Sektion enthalten")
            self.assertIn("## GitHub: ggml-org/llama.cpp", content,
                          "Bericht muss llama.cpp-Sektion enthalten")
            self.assertIn("## GitHub: ollama/ollama", content,
                          "Bericht muss ollama-Sektion enthalten")
            self.assertIn("## Slipstream neueste Entwicklungen", content,
                          "Bericht muss Slipstream-Sektion enthalten")

    # ======================== T9 ========================
    def test_t9_zweitlauf_bericht_angehangen(self):
        """T9: Zweiter Lauf in derselben Woche -> Bericht wird angehangen, nicht uberschrieben."""
        from agents.llm_scout.llm_scout import save_report

        with tempfile.TemporaryDirectory() as tmp_dir:
            report_dir = Path(tmp_dir) / "weekly-reports"
            report_dir.mkdir()
            filepath = report_dir / "llm_scout_kw42_2026.md"
            now = datetime(2026, 10, 20, 10, 0)

            # Erster Lauf
            save_report(filepath, "Bericht A - erster Lauf", now)
            content_after_first = filepath.read_text()
            self.assertIn("Bericht A", content_after_first)

            # Zweiter Lauf
            now2 = datetime(2026, 10, 20, 14, 0)
            save_report(filepath, "Bericht B - zweiter Lauf", now2)
            content_after_second = filepath.read_text()

            self.assertIn("Bericht A", content_after_second,
                          "Erster Bericht muss erhalten bleiben")
            self.assertIn("Bericht B", content_after_second,
                          "Zweiter Bericht muss angehangen sein")
            self.assertIn("Nachtrag", content_after_second,
                          "Nachtrag-Kennzeichnung muss vorhanden sein")

    # ======================== T9c (neu) ========================
    def test_t9c_llm_antwort_ohne_ollama_sektion(self):
        """Neuer Test: Modell-Antwort ohne die Ollama-Sektion -> Ollama-Sektion steht trotzdem im Bericht (via main())."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            sources_json = {
                "github": [
                    {"repo": "ggml-org/llama.cpp", "rss": "https://github.com/ggml-org/llama.cpp/releases.atom"},
                    {"repo": "ollama/ollama", "rss": "https://github.com/ollama/ollama/releases.atom"},
                ]
            }
            # LLM-Antwort ohne Ollama-Sektion
            llm_response = """# LLM Scout Weekly

## Hugging Face (neue Modelle)

Keine neuen Modelle in den letzten 7 Tagen.

## GitHub: ggml-org/llama.cpp

- **b650**: Neue Features.

## Slipstream neueste Entwicklungen

Keine neuen Entwicklungen in den letzten 7 Tagen.

## Fazit

Nur llama.cpp hat Updates."""

            exit_code, report_path, stderr_text = self._run_main(
                tmp_path,
                sources_json=sources_json,
                llm_response=llm_response
            )

            self.assertEqual(exit_code, 0, f"Exit-Code sollte 0 sein, ist {exit_code}")
            self.assertTrue(report_path.exists(), "Bericht muss existieren")

            content = report_path.read_text()
            # Ollama-Sektion fehlt im LLM-Output, muss von secure_report_sections nachgetragen werden
            self.assertIn("## GitHub: ollama/ollama", content,
                          "Ollama-Sektion muss trotz fehlendem LLM-Output im Bericht stehen")
            self.assertIn("## Hugging Face (neue Modelle)", content,
                          "Hugging-Face-Sektion muss vorhanden sein")
            self.assertIn("## GitHub: ggml-org/llama.cpp", content,
                          "llama.cpp-Sektion muss vorhanden sein")
            self.assertIn("## Slipstream neueste Entwicklungen", content,
                          "Slipstream-Sektion muss vorhanden sein")

    # ======================== T10 ========================
    def test_t10_slipstream_feed_leer_keine_entwicklungen(self):
        """T10: Slipstream-Repo-Feed ist leer -> Slipstream-Sektion mit 'Keine neuen Entwicklungen'."""
        from agents.llm_scout.llm_scout import (
            fetch_github_releases_for_repo,
            build_prompt_sections,
        )

        # Mock: leerer Feed
        mock_empty = b"""<?xml version="1.0"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
        </feed>"""

        def mock_get(url, **kwargs):
            resp = MagicMock()
            resp.status_code = 200
            resp.content = mock_empty
            return resp

        with patch("requests.get", side_effect=mock_get):
            _, slip_items = fetch_github_releases_for_repo(
                "https://github.com/Schero94/slipstream/releases.atom",
                "Schero94/slipstream"
            )

        self.assertEqual(len(slip_items), 0, "Leerer Feed sollte 0 Items liefern")

        # Prompt mit leeren Items bauen (Slipstream als Quelle konfiguriert)
        sources_config = {"github": [
            {"repo": "Schero94/slipstream", "rss": "https://github.com/Schero94/slipstream/releases.atom"}
        ]}
        prompt = build_prompt_sections([], sources_config)
        self.assertIn("## Slipstream neueste Entwicklungen", prompt,
                        "Slipstream-Sektion muss vorhanden sein")
        self.assertIn("Keine neuen Entwicklungen in den letzten 7 Tagen.", prompt,
                        "Leere Slipstream-Sektion muss 'Keine neuen Entwicklungen' enthalten")

    # ======================== T11 ========================
    def test_t11_funfites_repo_ohne_codeaenderung(self):
        """T11: sources.json-Erweiterung ohne Codeaenderung - funftes Repo wird erkannt."""
        from agents.llm_scout.llm_scout import load_sources

        with tempfile.TemporaryDirectory() as tmp_dir:
            sources_path = Path(tmp_dir) / "sources.json"
            sources_path.write_text(json.dumps({
                "github": [
                    {"repo": "ggml-org/llama.cpp", "rss": "https://github.com/ggml-org/llama.cpp/releases.atom"},
                    {"repo": "ollama/ollama", "rss": "https://github.com/ollama/ollama/releases.atom"},
                    {"repo": "huggingface/transformers", "rss": "https://github.com/huggingface/transformers/releases.atom"},
                    {"repo": "Schero94/slipstream", "rss": "https://github.com/Schero94/slipstream/releases.atom"},
                    {"repo": "test/repo", "rss": "https://github.com/test/repo/releases.atom"},
                ]
            }))

            sources = load_sources(sources_path)
            github_repos = sources.get("github", [])
            repo_names = [r["repo"] for r in github_repos]

            self.assertIn("test/repo", repo_names,
                          "Funftes Repo 'test/repo' muss erkannt werden")
            self.assertEqual(len(github_repos), 5,
                             "Alle 5 Repos mussen gelesen werden")

    # ======================== T12 ========================
    def test_t12_llm_scout_ladt_ohne_import_error(self):
        """T12: llm_scout.py laedt als Skript ohne ImportError (Bestandssicherung)."""
        import runpy
        # runpy.run_path laedt das Modul, aber fuhrt __main__ nicht aus
        try:
            runpy.run_path(str(_SCOUT_SCRIPT), run_name='__llm_scout_test__')
        except (ImportError, ModuleNotFoundError) as e:
            self.fail(f"Importfehler beim Laden von llm_scout.py: {e}")

    # ======================== T13 ========================
    def test_t13_repo_ohne_neue_eintraege_sektion_im_prompt_und_bericht(self):
        """T13: Repo ohne neue Eintraege -> Sektion mit 0 Eintraegen im Prompt- und Bericht."""
        from agents.llm_scout.llm_scout import (
            build_prompt_sections,
            fetch_github_releases_for_repo,
        )

        # Mock: leerer Feed
        mock_empty = b"""<?xml version="1.0"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
        </feed>"""

        def mock_get(url, **kwargs):
            resp = MagicMock()
            resp.status_code = 200
            resp.content = mock_empty
            return resp

        with patch("requests.get", side_effect=mock_get):
            _, items = fetch_github_releases_for_repo(
                "https://github.com/test/repo/releases.atom",
                "test/repo"
            )

        self.assertEqual(len(items), 0, "Leerer Feed sollte 0 Items liefern")

        # sources_config mit dieser Quelle
        sources_config = {"github": [
            {"repo": "test/repo", "rss": "https://github.com/test/repo/releases.atom"}
        ]}
        prompt = build_prompt_sections([], sources_config)

        # Sektion muss im Prompt sein, auch wenn leer
        # GitHub-Repos bekommen den Header "## GitHub: {repo_name}"
        self.assertIn("## GitHub: test/repo", prompt,
                       "Sektion fuer test/repo muss im Prompt sein")
        self.assertIn("Keine neuen Releases in den letzten 7 Tagen.", prompt,
                       "Leere Sektion muss 'Keine neuen Releases' enthalten")

    # ======================== T14 ========================
    def test_t14_drei_protokollstufen_feed_nur_alte_eintraege(self):
        """T14: Drei Protokollstufen mit Feed mit nur alten Eintraegen (fetched > 0, after_filter = 0)."""
        from agents.llm_scout.llm_scout import (
            fetch_github_releases_for_repo,
            write_source_run_log,
        )

        # Mock: Feed mit 3 Eintraegen, alle aelter als 7 Tage
        mock_old_feed = b"""<?xml version="1.0"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
          <entry>
            <title>Old Release 1</title>
            <link>https://github.com/test/repo/releases/tag/v1</link>
            <summary>Old</summary>
            <updated>2026-09-01T12:00:00Z</updated>
          </entry>
          <entry>
            <title>Old Release 2</title>
            <link>https://github.com/test/repo/releases/tag/v2</link>
            <summary>Old</summary>
            <updated>2026-09-02T12:00:00Z</updated>
          </entry>
          <entry>
            <title>Old Release 3</title>
            <link>https://github.com/test/repo/releases/tag/v3</link>
            <summary>Old</summary>
            <updated>2026-09-03T12:00:00Z</updated>
          </entry>
        </feed>"""

        def mock_get(url, **kwargs):
            resp = MagicMock()
            resp.status_code = 200
            resp.content = mock_old_feed
            return resp

        with patch("requests.get", side_effect=mock_get):
            fetched_count, filtered_items = fetch_github_releases_for_repo(
                "https://github.com/test/repo/releases.atom",
                "test/repo"
            )

        # fetched > 0 (API antwortete mit 3 Eintraegen)
        self.assertEqual(fetched_count, 3, f"fetched sollte 3 sein, ist {fetched_count}")
        # after_filter = 0 (alle aelter als 7 Tage)
        self.assertEqual(len(filtered_items), 0,
                         f"after_filter sollte 0 sein, ist {len(filtered_items)}")

        # Protokoll mit drei Stufen schreiben
        with tempfile.TemporaryDirectory() as tmp_dir:
            lab_dir = Path(tmp_dir)
            source_data = {
                "github:test/repo": {
                    "fetched": fetched_count,
                    "after_filter": len(filtered_items),
                    "new": len(filtered_items),  # new = after_filter (da alle bereits in DB oder gefiltert)
                    "sent_to_llm": []
                }
            }
            write_source_run_log(lab_dir, source_data)

            log_files = list(lab_dir.glob("source_run_log_*.jsonl"))
            self.assertEqual(len(log_files), 1)

            with open(log_files[0], 'r') as f:
                log_line = json.loads(f.readline())

            self.assertEqual(log_line["github:test/repo"]["fetched"], 3,
                             "fetched muss 3 sein")
            self.assertEqual(log_line["github:test/repo"]["after_filter"], 0,
                             "after_filter muss 0 sein")
            self.assertEqual(log_line["github:test/repo"]["new"], 0,
                             "new muss 0 sein")

    # ======================== T15 ========================
    def test_t15_warnung_ab_8_github_repos(self):
        """T15: Warnung auf stderr ab 8 GitHub-Repos ueber main() pruefen, Skript laeuft weiter."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            # 8 Repos
            repos = [{"repo": f"test/repo{i}", "rss": f"https://github.com/test/repo{i}/releases.atom"}
                     for i in range(8)]
            sources_json = {"github": repos}

            exit_code, report_path, stderr_text = self._run_main(
                tmp_path,
                sources_json=sources_json,
                llm_response="# LLM Scout Weekly\n\n## Fazit\n\nTest."
            )

            self.assertEqual(exit_code, 0, f"Exit-Code sollte 0 sein, ist {exit_code}")
            self.assertTrue(report_path.exists(), "Bericht muss existieren")
            # Warnung auf stderr
            self.assertIn("8", stderr_text,
                          f"stderr sollte '8' enthalten: {stderr_text}")
            self.assertIn("WARN", stderr_text.upper(),
                          f"stderr sollte 'WARN' enthalten: {stderr_text}")
            self.assertIn("GitHub-Repos", stderr_text,
                          f"stderr sollte 'GitHub-Repos' enthalten: {stderr_text}")

    # ======================== T16 ========================
    def test_t16_zweitlauf_woche_keine_neuen_eintraege_kein_nachtrag(self):
        """T16: zwei main()-Laufe in derselben Woche, der zweite ohne Neues -> Bericht byte-gleich."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            sources_json = {
                "github": [
                    {"repo": "ggml-org/llama.cpp", "rss": "https://github.com/ggml-org/llama.cpp/releases.atom"},
                ]
            }
            llm_response = "# LLM Scout Weekly\n\n## Hugging Face (neue Modelle)\n\nKeine neuen Modelle.\n\n## GitHub: ggml-org/llama.cpp\n\nKeine neuen Releases.\n\n## Slipstream neueste Entwicklungen\n\nKeine neuen Entwicklungen.\n\n## Fazit\n\nNichts Neues."

            # Erster Lauf: Erstellt den Bericht
            exit_code1, report_path, stderr1 = self._run_main(
                tmp_path,
                sources_json=sources_json,
                llm_response=llm_response
            )
            self.assertEqual(exit_code1, 0, f"Erster Lauf: Exit-Code sollte 0 sein, ist {exit_code1}")
            self.assertTrue(report_path.exists(), "Bericht muss nach erstem Lauf existieren")

            content_after_first = report_path.read_text()
            first_bytes = report_path.read_bytes()

            # Zweiter Lauf: Keine neuen Items, Bericht soll byte-gleich bleiben
            exit_code2, report_path2, stderr2 = self._run_main(
                tmp_path,
                sources_json=sources_json,
                llm_response=llm_response  # LLM wird nicht aufgerufen, da keine neuen Items
            )
            self.assertEqual(exit_code2, 0, f"Zweiter Lauf: Exit-Code sollte 0 sein, ist {exit_code2}")

            second_bytes = report_path.read_bytes()
            self.assertEqual(first_bytes, second_bytes,
                             "Bericht muss nach zweitem Lauf byte-gleich sein (kein Anhaengen)")

    # ======================== T17 ========================
    def test_t17_llm_laesst_item_weg_nicht_bewertet(self):
        """T17: LLM-Mock liefert alle Ueberschriften, laesst aber ein Item weg -> dessen URL steht im Bericht unter '## Nicht vom Modell bewertet'."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            sources_json = {
                "github": [
                    {"repo": "ggml-org/llama.cpp", "rss": "https://github.com/ggml-org/llama.cpp/releases.atom"},
                ]
            }
            # Zwei Items an das LLM, aber nur eines in der Antwort
            item1_url = "https://github.com/ggml-org/llama.cpp/releases/tag/b650"
            item2_url = "https://github.com/ggml-org/llama.cpp/releases/tag/b651"
            llm_response = f"""# LLM Scout Weekly

## Hugging Face (neue Modelle)

Keine neuen Modelle in den letzten 7 Tagen.

## GitHub: ggml-org/llama.cpp

- **b650**({item1_url}): Wichtige neue Features.

## Slipstream neueste Entwicklungen

Keine neuen Entwicklungen in den letzten 7 Tagen.

## Fazit

Nur b650 ist relevant."""

            gh_items = [
                {"source": "github:ggml-org/llama.cpp", "title": "b650", "url": item1_url, "summary": "Features"},
                {"source": "github:ggml-org/llama.cpp", "title": "b651", "url": item2_url, "summary": "Bugfix"},
            ]

            exit_code, report_path, stderr_text = self._run_main(
                tmp_path,
                sources_json=sources_json,
                gh_fetched_items={"github:ggml-org/llama.cpp": (2, gh_items)},
                llm_response=llm_response
            )

            self.assertEqual(exit_code, 0, f"Exit-Code sollte 0 sein, ist {exit_code}")
            self.assertTrue(report_path.exists(), "Bericht muss existieren")

            content = report_path.read_text()
            self.assertIn("## Nicht vom Modell bewertet", content,
                          "Bericht muss 'Nicht vom Modell bewertet'-Sektion enthalten")
            self.assertIn(item2_url, content,
                          f"Fehlende Item-URL ({item2_url}) muss im Bericht stehen")
            self.assertIn("b651", content,
                          "Fehlender Titel 'b651' muss im Bericht stehen")

    # ======================== T18 ========================
    def test_t18_llm_fazit_und_fehlende_sektion_vor_fazit(self):
        """T18: LLM-Mock mit '## Fazit' und fehlender ollama-Sektion -> ollama-Sektion steht vor '## Fazit'."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            sources_json = {
                "github": [
                    {"repo": "ggml-org/llama.cpp", "rss": "https://github.com/ggml-org/llama.cpp/releases.atom"},
                    {"repo": "ollama/ollama", "rss": "https://github.com/ollama/ollama/releases.atom"},
                ]
            }
            # LLM-Antwort ohne ollama-Sektion, aber mit Fazit
            llm_response = """# LLM Scout Weekly

## Hugging Face (neue Modelle)

Keine neuen Modelle in den letzten 7 Tagen.

## GitHub: ggml-org/llama.cpp

Keine neuen Releases in den letzten 7 Tagen.

## Slipstream neueste Entwicklungen

Keine neuen Entwicklungen in den letzten 7 Tagen.

## Fazit

Nichts Neues."""

            exit_code, report_path, stderr_text = self._run_main(
                tmp_path,
                sources_json=sources_json,
                llm_response=llm_response
            )

            self.assertEqual(exit_code, 0, f"Exit-Code sollte 0 sein, ist {exit_code}")
            self.assertTrue(report_path.exists(), "Bericht muss existieren")

            content = report_path.read_text()
            self.assertIn("## GitHub: ollama/ollama", content,
                          "Ollama-Sektion muss im Bericht stehen")
            self.assertIn("## Fazit", content,
                          "Fazit-Sektion muss vorhanden sein")
            # Ollama-Sektion muss VOR Fazit stehen
            ollama_pos = content.index("## GitHub: ollama/ollama")
            fazit_pos = content.index("## Fazit")
            self.assertLess(ollama_pos, fazit_pos,
                            "Ollama-Sektion muss vor '## Fazit' eingefuegt werden")

    # ======================== T19 ========================
    def test_t19_system_prompt_enthalt_nicht_ignoriere_oder_top35(self):
        """T19: System-Prompt enthaelt nicht 'ignoriere sie' und nicht 'Top 3-5'."""
        from agents.llm_scout.llm_scout import call_llm_for_evaluation
        import re

        # call_llm_for_evaluation bauen den system_prompt intern.
        # Wir pruefen den Source-Code der Funktion auf die verbotenen Phrasen.
        import inspect
        source = inspect.getsource(call_llm_for_evaluation)

        self.assertNotIn("ignoriere sie", source.lower(),
                         "System-Prompt darf 'ignoriere sie' nicht enthalten")
        self.assertNotIn("Top 3-5", source,
                         "System-Prompt darf 'Top 3-5' nicht enthalten")
        self.assertNotIn("top 3-5", source.lower(),
                         "System-Prompt darf 'top 3-5' nicht enthalten")
        # Stattdessen muss die JEDES-Item-Regel da sein
        self.assertIn("JEDES", source,
                      "System-Prompt muss 'JEDES' enthalten")
        self.assertIn("verworfen", source,
                      "System-Prompt muss 'verworfen' enthalten")

    # ======================== T20 ========================
    def test_t20_fazit_variante_regex_einfuegepunkt(self):
        """T20: Ueberschriften '## Fazit und Empfehlung', '## Fazit: lohnt sich nicht' und
        '## Fazit' als letzte Zeile ohne Zeilenumbruch -> in allen drei Faellen stehen
        fehlende Sektion UND fehlender Item-Link im Ergebnis, vor der Fazit-Zeile."""
        from agents.llm_scout.llm_scout import secure_report_sections

        sources_config = {
            "github": [
                {"repo": "ggml-org/llama.cpp", "rss": "https://github.com/ggml-org/llama.cpp/releases.atom"},
                {"repo": "ollama/ollama", "rss": "https://github.com/ollama/ollama/releases.atom"},
            ]
        }
        evaluated = [
            {"source": "github:ggml-org/llama.cpp", "title": "b650",
             "url": "https://github.com/ggml-org/llama.cpp/releases/tag/b650", "summary": "Features"},
            {"source": "github:ggml-org/llama.cpp", "title": "b651",
             "url": "https://github.com/ggml-org/llama.cpp/releases/tag/b651", "summary": "Bugfix"},
        ]

        # Drei verschiedene Fazit-Varianten testen
        fazit_variants = [
            "## Fazit und Empfehlung\n\nDas ist das Fazit.",
            "## Fazit: lohnt sich nicht\n\nKein Update notwendig.",
            "## Fazit",  # letzte Zeile ohne Zeilenumbruch
        ]

        for fazit_heading in fazit_variants:
            with self.subTest(fazit_heading=fazit_heading):
                llm_report = f"""# LLM Scout Weekly

## Hugging Face (neue Modelle)

Keine neuen Modelle in den letzten 7 Tagen.

## GitHub: ggml-org/llama.cpp

- **b650**(https://github.com/ggml-org/llama.cpp/releases/tag/b650): Features.

## Slipstream neueste Entwicklungen

Keine neuen Entwicklungen in den letzten 7 Tagen.

{fazit_heading}"""

                result = secure_report_sections(llm_report, evaluated, sources_config)

                # Fehlende ollama-Sektion muss im Ergebnis sein
                self.assertIn("## GitHub: ollama/ollama", result,
                              f"Fehlende Sektion muss im Ergebnis sein (Fazit: {fazit_heading!r})")
                # Fehlendes Item b651 muss unter "Nicht bewertet" stehen
                self.assertIn("## Nicht vom Modell bewertet", result,
                              f"'Nicht bewertet'-Sektion muss im Ergebnis sein (Fazit: {fazit_heading!r})")
                self.assertIn("b651", result,
                              f"Fehlender Titel 'b651' muss im Ergebnis sein (Fazit: {fazit_heading!r})")
                # Beide Ergaenzungen mussen VOR der Fazit-Zeile stehen
                ollama_pos = result.index("## GitHub: ollama/ollama")
                fazit_pos = result.index("## Fazit")
                self.assertLess(ollama_pos, fazit_pos,
                                f"Ollama-Sektion muss vor Fazit stehen (Fazit: {fazit_heading!r})")
                nicht_bewertet_pos = result.index("## Nicht vom Modell bewertet")
                self.assertLess(nicht_bewertet_pos, fazit_pos,
                                f"'Nicht bewertet' muss vor Fazit stehen (Fazit: {fazit_heading!r})")

    # ======================== T21 ========================
    def test_t21_url_pruefung_exakt_kein_prefix_treffer(self):
        """T21: Bericht enthaelt nur '.../tag/b11724', evaluated hat '.../tag/b1172' ->
        b1172 steht unter '## Nicht vom Modell bewertet' (kein Prefix-False-Positive)."""
        from agents.llm_scout.llm_scout import secure_report_sections

        sources_config = {
            "github": [
                {"repo": "ggml-org/llama.cpp", "rss": "https://github.com/ggml-org/llama.cpp/releases.atom"},
            ]
        }
        # evaluated hat die kuerzere URL b1172
        evaluated = [
            {"source": "github:ggml-org/llama.cpp", "title": "b1172",
             "url": "https://github.com/ggml-org/llama.cpp/releases/tag/b1172", "summary": "Release"},
        ]
        # Bericht enthaelt nur die laengere URL b11724 (kein Treffer fuer b1172)
        llm_report = """# LLM Scout Weekly

## Hugging Face (neue Modelle)

Keine neuen Modelle in den letzten 7 Tagen.

## GitHub: ggml-org/llama.cpp

- **b11724**(https://github.com/ggml-org/llama.cpp/releases/tag/b11724): Anderes Release.

## Slipstream neueste Entwicklungen

Keine neuen Entwicklungen in den letzten 7 Tagen.

## Fazit

b11724 ist relevant."""

        result = secure_report_sections(llm_report, evaluated, sources_config)

        # b1172 muss unter "Nicht bewertet" stehen (kein False-Positive durch b11724)
        self.assertIn("## Nicht vom Modell bewertet", result,
                      "'Nicht bewertet'-Sektion muss im Ergebnis sein")
        self.assertIn("b1172", result,
                      "Titel 'b1172' muss im Ergebnis sein")
        # Die spezifische URL muss im "Nicht bewertet"-Teil stehen
        nicht_bewertet_pos = result.index("## Nicht vom Modell bewertet")
        fazit_pos = result.index("## Fazit")
        self.assertLess(nicht_bewertet_pos, fazit_pos,
                        "'Nicht bewertet' muss vor Fazit stehen")
        # Der Abschnitt zwischen "Nicht bewertet" und "Fazit" muss die URL enthalten
        zwischen = result[nicht_bewertet_pos:fazit_pos]
        self.assertIn("https://github.com/ggml-org/llama.cpp/releases/tag/b1172", zwischen,
                      "URL von b1172 muss im 'Nicht bewertet'-Teil stehen")


if __name__ == "__main__":
    unittest.main()
