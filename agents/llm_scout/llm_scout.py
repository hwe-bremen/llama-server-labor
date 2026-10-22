#!/usr/bin/env python3
"""
Local LLM Scout: Wöchentliche Zusammenfassung neuer lokaler LLM-Entwicklungen.
Nutzt Hugging Face API, GitHub RSS und llama-server für die Evaluation.

Erweitert um pro-Quellen-Protokoll, sources.json-Konfiguration,
Slipstream als eigene Quelle, und pro-Quellen-Prompt-Präsentation.
"""

import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

import feedparser
import requests

# week_key.py liegt im gleichen Verzeichnis; beim Start als Skript (__main__)
# ist ein relativer Import nicht moeglich -> sys.path anpassen (wie in send_scout_email.py)
_script_dir = str(Path(__file__).resolve().parent)
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)
from week_key import week_key_for_filename

# --- KONFIGURATION ---

# Pfade
BASE_DIR = Path(os.getenv("LAB_DIR", Path.home() / "lab"))
DB_PATH = BASE_DIR / "llm_scout.db"
REPORT_DIR = BASE_DIR / "weekly-reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# API Endpunkte
LLAMA_SERVER_URL = os.getenv("LLAMA_SERVER_URL", "http://localhost:8080")
HF_API_URL = "https://huggingface.co/api/models"
GITHUB_RELEASES_RSS = [
    "https://github.com/ggml-org/llama.cpp/releases.atom",
    "https://github.com/ollama/ollama/releases.atom",
    "https://github.com/huggingface/transformers/releases.atom"
]

# Modell Konfiguration
# Wir nutzen das von dir genannte Modell. Falls es nicht läuft, fallback auf Qwen2.5-14B
MODEL_NAME = os.getenv("SCOUT_MODEL", "unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL")

# Zeitfenster: Nur Items der letzten N Tage betrachten (Standard: 7 Tage für "wöchentlich")
LOOKBACK_DAYS = 7

# Top-N Items pro Quelle für den LLM-Prompt
ITEMS_PER_SOURCE = 3

# Pfad zur sources.json – liegt neben dem Script im Repo
_SOURCES_JSON_PATH = Path(__file__).resolve().parent / "sources.json"

# Slipstream-Repo-ID (exakt)
SLIPSTREAM_REPO = "Schero94/slipstream"


# --- QUELLENKONFIGURATION (A2) ---

def load_sources(sources_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Liest die sources.json und gibt das Quellen-Dictionary zurück.

    Erkennt nur den Key 'github'. Unbekannte Keys werden mit
    einer stderr-Warnung ignoriert.

    Args:
        sources_path: Pfad zur sources.json. Default: neben dem Script.

    Returns:
        Dictionary mit Quellen, z. B.:
        {"github": [{"repo": "ggml-org/llama.cpp", "rss": "..."}, ...]}

    Raises:
        SystemExit(1): Datei fehlt oder ist ungültiges JSON.
    """
    path = sources_path or _SOURCES_JSON_PATH

    if not path.exists():
        print(f"sources.json nicht gefunden unter {path}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"sources.json ist ungültiges JSON: {e}", file=sys.stderr)
        sys.exit(1)

    # Nur bekannte Keys verarbeiten
    result = {}
    for key in data:
        if key == "github":
            result[key] = data[key]
        else:
            print(f"Warnung: Unbekannter Quellentyp '{key}' in sources.json, wird ignoriert.",
                  file=sys.stderr)

    return result


# --- HILFSFUNKTIONEN ---

def init_db(conn: sqlite3.Connection) -> None:
    """Erstellt die Tabelle, falls nicht vorhanden."""
    conn.execute("""
                  CREATE TABLE IF NOT EXISTS processed_items
                  (
                      id
                      INTEGER
                      PRIMARY
                      KEY
                      AUTOINCREMENT,
                      source
                      TEXT
                      NOT
                      NULL,
                      title
                      TEXT
                      NOT
                      NULL,
                      url
                      TEXT
                      UNIQUE
                      NOT
                      NULL,
                      processed_at
                      TIMESTAMP
                      DEFAULT
                      CURRENT_TIMESTAMP
                  )
                  """)
    conn.commit()


def is_new_item(conn: sqlite3.Connection, url: str) -> bool:
    """Prüft, ob die URL bereits verarbeitet wurde."""
    cursor = conn.execute("SELECT 1 FROM processed_items WHERE url=?", (url,))
    return cursor.fetchone() is None


def mark_as_processed(conn: sqlite3.Connection, source: str, title: str, url: str) -> None:
    """Markiert ein Item als verarbeitet."""
    try:
        conn.execute(
            "INSERT INTO processed_items (source, title, url) VALUES (?, ?, ?)",
            (source, title, url)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Bereits vorhanden, ignorieren


# --- SOURCE-TAG-ZUORDNUNG (A5) ---

def assign_source_tags(item: Dict[str, Any], source_key: str) -> Dict[str, Any]:
    """
    Weist einem Item den korrekten source-Tag zu.

    Slipstream-Items aus Schero94/slipstream bekommen den Tag 'slipstream',
    alle anderen GitHub-Items bekommen 'github:<repo>'.

    Args:
        item: Das Item-Dictionary (wird nicht verändert).
        source_key: Der Quellen-Schlüssel, z. B. 'github:ggml-org/llama.cpp',
                    'slipstream', 'huggingface'.

    Returns:
        Das Item mit dem korrigierten 'source'-Feld.
    """
    result = dict(item)
    result["source"] = source_key
    return result


def get_source_key_for_repo(repo_name: str) -> str:
    """
    Bildet den source-Key für ein GitHub-Repo.

    Schero94/slipstream -> 'slipstream'
    ggml-org/llama.cpp -> 'github:ggml-org/llama.cpp'
    """
    if repo_name == SLIPSTREAM_REPO:
        return "slipstream"
    return f"github:{repo_name}"


# --- DATEN HOLEN (unverändert, aber pro-Repo aufgeteilt) ---

def fetch_hf_trending() -> tuple:
    """
    Holt trending Modelle von Hugging Face.
    Filtert nach GGUF, sortiert nach Likes. Nimmt Modelle die
    neu sind (<30 Tage) ODER viele Downloads haben (>1000).

    Returns:
        Tuple (fetched_count, items_after_filter) wobei fetched_count die
        Anzahl der Modelle aus der API-Antwort ist (vor jeglichem Filter)
        und items_after_filter die gefilterte Liste.
    """
    items = []
    fetched_count = 0
    try:
        params = {
            "sort": "likes",
            "direction": "-1",
            "limit": 50,
            "filter": "gguf"
        }
        response = requests.get(HF_API_URL, params=params, timeout=10)
        response.raise_for_status()
        models = response.json()
        fetched_count = len(models)

        now = datetime.now(tz=__import__('datetime').timezone.utc)
        cutoff = now - timedelta(days=30)

        for model in models:
            created = model.get("createdAt", "")
            likes = model.get("likes", 0)
            downloads = model.get("downloads", 0)

            # Kriterium: neu ODER populär genug
            is_new = False
            if created:
                try:
                    created_dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    is_new = created_dt > cutoff
                except Exception:
                    pass

            if is_new or downloads > 1000:
                items.append({
                    "source": "huggingface",
                    "title": model["id"],
                    "url": f"https://huggingface.co/{model['id']}",
                    "summary": f"Likes: {likes}, Downloads: {downloads}, Tags: {', '.join(model['tags'][:5])}",
                    "likes": likes
                })
    except Exception as e:
        print(f"Fehler beim Abrufen von Hugging Face: {e}", file=sys.stderr)

    items.sort(key=lambda x: x.get("likes", 0), reverse=True)
    return (fetched_count, items)


def fetch_github_releases_for_repo(rss_url: str, repo_name: str) -> tuple:
    """
    Holt neue Releases von einem einzelnen GitHub Repository via RSS.

    Args:
        rss_url: Die RSS-URL des Repos.
        repo_name: Der Repo-Name, z. B. 'ggml-org/llama.cpp'.

    Returns:
        Tuple (fetched_count, items_after_filter) wobei fetched_count die
        Anzahl der Eintraege im Feed VOR dem 7-Tage-Filter ist und
        items_after_filter nur die Items nach dem Filter.
    """
    items = []
    cutoff_date = datetime.now() - timedelta(days=LOOKBACK_DAYS)
    source_key = get_source_key_for_repo(repo_name)
    fetched_count = 0

    try:
        # Abruf ueber requests (nutzt certifi): feedparser/urllib scheitert mit dem
        # python.org-Python auf macOS an der Zertifikatspruefung -> still 0 Eintraege.
        resp = requests.get(rss_url, timeout=15, headers={"User-Agent": "llm-scout-lab/1.0"})
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
        if feed.bozo and not feed.entries:
            print(f"  WARNUNG {rss_url}: Feed nicht lesbar ({feed.get('bozo_exception')})", file=sys.stderr)
            return (0, items)
        fetched_count = len(feed.entries)
        print(f"  RSS {rss_url}: {fetched_count} fetched, cutoff: {cutoff_date.strftime('%Y-%m-%d')}")
        for entry in feed.entries:
            # Datum prüfen – updated_parsed ist time.struct_time (UTC)
            updated_parsed = getattr(entry, 'updated_parsed', None)
            if updated_parsed:
                updated_dt = datetime(*updated_parsed[:6])
                if updated_dt > cutoff_date:
                    items.append({
                        "source": source_key,
                        "title": entry.title,
                        "url": entry.link,
                        "summary": entry.summary[:200] + "..." if len(entry.summary) > 200 else entry.summary
                    })
            else:
                print(f"    (kein Datum) {entry.title}")
    except Exception as e:
        print(f"Fehler beim Abrufen von {rss_url}: {e}", file=sys.stderr)

    return (fetched_count, items)



# --- PRO-QUELLEN-SELEKTION (A4) ---

def select_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Was tatsaechlich bewertet wird: Top N pro Quelle (Kontext sparen).
    Nur diese Items werden nach einem gespeicherten Bericht als verarbeitet markiert.

    Im Gegensatz zum alten Code (global Top 3 HF + Top 3 GH) wird nun
    pro source-Key unabhängig selektiert.
    """
    # Items nach source gruppieren
    by_source: Dict[str, List[Dict[str, Any]]] = {}
    for item in items:
        src = item.get("source", "unknown")
        by_source.setdefault(src, []).append(item)

    selected = []
    for src, src_items in by_source.items():
        selected.extend(src_items[:ITEMS_PER_SOURCE])
    return selected


# --- PRO-QUELLEN-PROTOKOLL (A1) ---

def write_source_run_log(lab_dir: Path, source_data: Dict[str, Dict[str, Any]]) -> None:
    """
    Schreibt das Quellenverteilungsprotokoll als JSONL-Datei.

    Jede Quelle hat vier Stufen:
        - fetched: Eintraege im Feed/API-Antwort VOR jedem Filter
        - after_filter: nach 7-Tage-Filter
        - new: nach DB-Abgleich (noch nicht verarbeitet)
        - sent_to_llm: Items die tatsaechlich an das LLM gesendet wurden

    Args:
        lab_dir: Das LAB_DIR-Verzeichnis.
        source_data: Dictionary mit pro Quelle:
            {
                "huggingface": {"fetched": 50, "after_filter": 5, "new": 3, "sent_to_llm": [...]},
                ...
            }
    """
    iso_year, iso_week, _ = datetime.now().isocalendar()
    log_filename = f"source_run_log_kw{iso_week}_{iso_year}.jsonl"
    log_path = lab_dir / log_filename

    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(source_data, ensure_ascii=False) + "\n")


# --- LLM-PROMPT MIT PRO-QUELLEN-SEKTIONEN (A4, A6) ---

def build_prompt_sections(items: List[Dict[str, Any]], sources_config: Dict[str, Any]) -> str:
    """
    Baut den User-Prompt mit pro-Quellen-Sektionen.

    Jede konfigurierte Quelle (aus sources_config) und Hugging Face erscheinen
    als eigene Markdown-Sektion – auch wenn keine Items vorhanden sind.
    Der Code baut das Geruest, das LLM fuellt die Bewertungen.

    Args:
        items: Alle Items (nach DB-Filter).
        sources_config: Die sources.json-Konfiguration.
    """
    # Items nach source gruppieren
    by_source: Dict[str, List[Dict[str, Any]]] = {}
    for item in items:
        src = item.get("source", "unknown")
        by_source.setdefault(src, []).append(item)

    sections = []

    # Hugging Face Sektion (immer vorhanden)
    hf_items = by_source.get("huggingface", [])
    sections.append("## Hugging Face (neue Modelle)")
    if hf_items:
        for it in hf_items[:ITEMS_PER_SOURCE]:
            sections.append(f"- [{it['title']}]({it['url']}): {it['summary']}")
    else:
        sections.append("Keine neuen Modelle in den letzten 7 Tagen.")
    sections.append("")

    # GitHub-Sektionen (jedes konfigurierte Repo separat, auch ohne Items)
    github_repos = sources_config.get("github", [])
    for repo_config in github_repos:
        repo_name = repo_config["repo"]
        if repo_name == SLIPSTREAM_REPO:
            continue  # Slipstream wird separat behandelt
        source_key = get_source_key_for_repo(repo_name)
        repo_items = by_source.get(source_key, [])
        sections.append(f"## GitHub: {repo_name}")
        if repo_items:
            for it in repo_items[:ITEMS_PER_SOURCE]:
                sections.append(f"- [{it['title']}]({it['url']}): {it['summary']}")
        else:
            sections.append("Keine neuen Releases in den letzten 7 Tagen.")
        sections.append("")

    # Slipstream-Sektion (immer vorhanden)
    slip_items = by_source.get("slipstream", [])
    sections.append("## Slipstream neueste Entwicklungen")
    if slip_items:
        for it in slip_items[:ITEMS_PER_SOURCE]:
            sections.append(f"- [{it['title']}]({it['url']}): {it['summary']}")
    else:
        sections.append("Keine neuen Entwicklungen in den letzten 7 Tagen.")

    return "\n".join(sections)


def call_llm_for_evaluation(items: List[Dict[str, Any]],
                            sources_config: Dict[str, Any]) -> str:
    """
    Sendet die Liste der neuen Items an llama-server zur Bewertung.
    Nutzt pro-Quellen-Prompt-Struktur (A4, A6).

    Der Prompt enthält Sektionen für ALLE konfigurierten Quellen, auch wenn
    keine Items vorhanden sind. Das LLM bewertet jede Sektion.

    Args:
        items: Liste aller neuen Items (nach DB-Filter).
        sources_config: Die sources.json-Konfiguration.
    """
    # Prompt Konstruktion
    system_prompt = """
    Du bist ein Experte für lokale LLM-Infrastruktur (llama.cpp, Ollama, GGUF).
    Deine Aufgabe ist es, eine Liste neuer Modell-Releases und Tool-Updates zu bewerten.

    Bewerte jede Quelle getrennt. Für jede Quelle, die keine neuen Items hat,
    schreibe explizit 'Keine neuen Entwicklungen in den letzten 7 Tagen.'
    Verwerfe kein Item ohne eine einzeilige Begründung.

    Kriterien für Relevanz:
    1. Modellgröße: Ideal < 15GB in Q4_K_M Quantisierung (passend für M4 Mac mit 48GB RAM).
    2. Kompatibilität: Muss GGUF unterstützen oder für llama.cpp/Ollama tauglich sein.
    3. Leistung: Zeigt es signifikante Verbesserungen in Benchmarks (MMLU, GPQA, etc.)?
    4. Lizenz: Open Source (Apache 2.0, MIT, etc.) bevorzugt.
    5. Sprache: Deutsch-Unterstützung ist ein Bonus.

    Gib die Top 3-5 interessantesten Entwicklungen zurück.
    Wenn es nur kleine Bugfixes sind, ignoriere sie.

    Ausgabeformat:
    # LLM Scout Weekly

    ## Hugging Face (neue Modelle)
    - **[Modellname](Link)**: Kurze Begründung (Größe, Leistung, Sprache).
    (oder: „Keine neuen Modelle in den letzten 7 Tagen.")

    ## GitHub: ggml-org/llama.cpp
    - **[Release-Titel](Link)**: Wichtige neue Features.
    (oder: „Keine neuen Releases in den letzten 7 Tagen.")

    ## GitHub: ollama/ollama
    ...

    ## Slipstream neueste Entwicklungen
    - **[Release-Titel](Link)**: Wichtige neue Features.
    (oder: „Keine neuen Entwicklungen in den letzten 7 Tagen.")

    ## Fazit
    Ein Satz zusammenfassend, ob sich ein Update lohnt.
    """

    # Pro-Quellen-Prompt mit Sektionen (alle konfigurierten Quellen, auch ohne Items)
    items_text = build_prompt_sections(items, sources_config)

    user_prompt = f"""
    Hier sind die neuen Entwicklungen der letzten Woche:

    {items_text}

    Bitte bewerte jede Quelle getrennt und erstelle das Infopaper.
    """

    # API Call an llama-server
    # Wir nutzen das OpenAI-kompatible Format, da es am weitesten verbreitet ist in llama.cpp
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 4096,
        "stream": False,
        # Qwen3.x denkt sonst ins max_tokens-Budget hinein -> leerer content
        "chat_template_kwargs": {"enable_thinking": False}
    }

    try:
        print(f"Frage wird an LLM ({MODEL_NAME}) gestellt...")
        response = requests.post(
            f"{LLAMA_SERVER_URL}/v1/chat/completions",
            json=payload,
            timeout=120
        )
        print(f"  HTTP-Status: {response.status_code}")
        if response.status_code != 200:
            print(f"  Antwort: {response.text[:500]}")
        response.raise_for_status()
        result = response.json()
        print(f"  Roh-JSON: {json.dumps(result, indent=2)[:1000]}")
        content = (result["choices"][0]["message"].get("content") or "").strip()
        print(f"  Antwortlänge: {len(content)} Zeichen")
    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(f"keine Verbindung zu {LLAMA_SERVER_URL}") from e
    if not content:
        raise RuntimeError("Modell lieferte leeren Inhalt")
    return content


def save_report(filepath: Path, report_content: str, now: datetime) -> None:
    """
    Schreibt den LLM-Bericht in die Datei.

    A1: Existiert die Datei bereits (Zweitlauf derselben ISO-KW), wird der
    neue Output als klar gekennzeichneter Nachtrag angehängt, statt den
    Erstbericht zu überschreiben.
    """
    iso_year, iso_week, _ = now.isocalendar()
    date_str = now.strftime("%Y-%m-%d %H:%M")

    if filepath.exists():
        # Zweitlauf: Nachtrag anhängen, Erstbericht bleibt byte-identisch
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(f"\n\n---\n\n")
            f.write(f"## Nachtrag KW{iso_week}_{iso_year} ({date_str})\n\n")
            f.write(report_content)
    else:
        # Erstlauf: Datei neu anlegen
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)


def router_ready(timeout: float = 5.0) -> bool:
    """Laeuft der llama-server? Ohne ihn gar nicht erst anfangen (nichts markieren)."""
    try:
        return requests.get(f"{LLAMA_SERVER_URL}/v1/models", timeout=timeout).status_code == 200
    except Exception:
        return False


def main():
    # Exit-Code-Semantik:
    #   0 = Erfolg (inkl. "keine neuen Items")
    #   1 = kritischer Fehler (API-Abruf, LLM-Evaluation, DB-Fehler)
    #   2 = llama-server nicht erreichbar
    print("--- Local LLM Scout gestartet ---")

    # (A2) sources.json laden – vor jeglicher DB-Interaktion
    try:
        sources_config = load_sources()
    except SystemExit:
        raise  # Exit 1, keine DB-Änderung

    # Warnung bei 8+ GitHub-Repos (stderr), Lauf wird fortgesetzt
    github_repos = sources_config.get("github", [])
    if len(github_repos) >= 8:
        print(f"[WARN] {len(github_repos)} GitHub-Repos konfiguriert (>= 8). "
              "Das kann zu langen Abrufzeiten und großen Prompts führen.", file=sys.stderr)

    if not router_ready():
        print(f"llama-server unter {LLAMA_SERVER_URL} nicht erreichbar – nichts geholt, nichts markiert.",
              file=sys.stderr)
        sys.exit(2)

    try:
        # DB Initialisierung
        conn = sqlite3.connect(DB_PATH)
        init_db(conn)

        # 1. Daten holen
        print("Hole Daten von Hugging Face und GitHub...")
        hf_fetched, hf_items = fetch_hf_trending()

        # GitHub-Repos pro-Repo holen (aus sources.json) – Slipstream wird hier mitgeholt
        gh_items_by_repo: Dict[str, List[Dict[str, Any]]] = {}
        gh_fetched_by_repo: Dict[str, int] = {}
        for repo_config in github_repos:
            repo_name = repo_config["repo"]
            rss_url = repo_config["rss"]
            source_key = get_source_key_for_repo(repo_name)
            fetched_count, repo_items = fetch_github_releases_for_repo(rss_url, repo_name)
            gh_items_by_repo[source_key] = repo_items
            gh_fetched_by_repo[source_key] = fetched_count

        # Alle Items zusammenfassen (Slipstream ist Teil von gh_items_by_repo)
        all_items = list(hf_items)
        for source_key, repo_items in gh_items_by_repo.items():
            all_items.extend(repo_items)

        total_gh = sum(len(v) for v in gh_items_by_repo.values())
        print(f"Gesamt gefunden: {len(hf_items)} HF + {total_gh} GH = {len(all_items)} Items")

        # 2. Filtern (nur neue) – noch NICHT markieren
        new_items = []
        for item in all_items:
            if is_new_item(conn, item['url']):
                new_items.append(item)
            else:
                print(f"  (bereits verarbeitet) {item['title']}")
        print(f"Neue Items (nach DB-Abgleich): {len(new_items)}")

        # Neue Items pro Quelle gruppieren für das Protokoll
        new_by_source: Dict[str, List[Dict[str, Any]]] = {}
        for item in new_items:
            src = item.get("source", "unknown")
            new_by_source.setdefault(src, []).append(item)

        # (A1) Pro-Quellen-Protokoll bauen
        # fetched counts: API-Antwort VOR jeglichem Filter
        # after_filter counts: nach 7-Tage-Filter
        # new counts: nach DB-Abgleich
        # sent_to_llm: Items die an das LLM gesendet werden

        # (A4) Pro-Quellen-Selektion
        evaluated = select_items(new_items)
        evaluated_by_source: Dict[str, List[Dict[str, Any]]] = {}
        for item in evaluated:
            src = item.get("source", "unknown")
            evaluated_by_source.setdefault(src, []).append(item)

        # sent_to_llm: Liste von {url, title} pro Quelle
        sent_to_llm: Dict[str, List[Dict[str, Any]]] = {}
        for src, src_eval in evaluated_by_source.items():
            sent_to_llm[src] = [{"url": it["url"], "title": it["title"]} for it in src_eval]

        # Alle konfigurierten Quellen im Protokoll (auch leere)
        source_log_data: Dict[str, Dict[str, Any]] = {}
        source_log_data["huggingface"] = {
            "fetched": hf_fetched,
            "after_filter": len(hf_items),
            "new": len(new_by_source.get("huggingface", [])),
            "sent_to_llm": sent_to_llm.get("huggingface", [])
        }
        for repo_config in github_repos:
            repo_name = repo_config["repo"]
            source_key = get_source_key_for_repo(repo_name)
            source_log_data[source_key] = {
                "fetched": gh_fetched_by_repo.get(source_key, 0),
                "after_filter": len(gh_items_by_repo.get(source_key, [])),
                "new": len(new_by_source.get(source_key, [])),
                "sent_to_llm": sent_to_llm.get(source_key, [])
            }

        # (A1) Protokoll schreiben – VOR dem LLM-Aufruf
        write_source_run_log(BASE_DIR, source_log_data)
        print(f"Quellenprotokoll geschrieben: source_run_log_kw*.jsonl")

        # Bericht-Logik:
        # - Erster Lauf der Woche (Bericht existiert noch nicht):
        #   Immer Bericht mit allen Sektionen schreiben (auch wenn leer)
        # - Weiterer Lauf derselben Woche ohne neue Items:
        #   Nichts anhaengen, Bericht bleibt unveraendert
        # - Weiterer Lauf mit neuen Items:
        #   Wie bisher anhaengen
        os.makedirs(REPORT_DIR, exist_ok=True)
        now = datetime.now()
        filename = week_key_for_filename(now)
        filepath = REPORT_DIR / filename
        report_exists = filepath.exists()

        if not new_items and report_exists:
            # Kein neuer Input, Bericht existiert bereits -> nichts tun
            conn.close()
            print("Keine neuen Items und Bericht existiert bereits. Skript beendet.")
            sys.exit(0)

        # LLM aufrufen (mit allen Sektionen, auch wenn leer)
        print(f"Bewerte Items ({len(new_items)} neue, {len(evaluated)} fuer LLM)...")
        report_content = call_llm_for_evaluation(new_items, sources_config)

        # Bericht speichern
        save_report(filepath, report_content, now)
        print(f"Bericht gespeichert unter: {filepath}")

        # 5. Erst jetzt markieren – und nur, was wirklich bewertet wurde
        for item in evaluated:
            mark_as_processed(conn, item['source'], item['title'], item['url'])
        conn.close()
        print(f"Als verarbeitet markiert: {len(evaluated)} (Rest bleibt fuer die naechste Woche offen)")
        print("--- Skript beendet ---")
        sys.exit(0)

    except Exception as e:
        print(f"Kritischer Fehler: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
