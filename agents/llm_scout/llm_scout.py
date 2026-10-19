#!/usr/bin/env python3
"""
Local LLM Scout: Wöchentliche Zusammenfassung neuer lokaler LLM-Entwicklungen.
Nutzt Hugging Face API, GitHub RSS und llama-server für die Evaluation.
"""

import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

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


def fetch_hf_trending() -> List[Dict[str, Any]]:
    """
    Holt trending Modelle von Hugging Face.
    Filtert nach GGUF, sortiert nach Likes. Nimmt Modelle die
    neu sind (<30 Tage) ODER viele Downloads haben (>1000).
    """
    items = []
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
    return items


def fetch_github_releases() -> List[Dict[str, Any]]:
    """
    Holt neue Releases von GitHub Repositories via RSS.
    """
    items = []
    cutoff_date = datetime.now() - timedelta(days=LOOKBACK_DAYS)

    for rss_url in GITHUB_RELEASES_RSS:
        try:
            # Abruf ueber requests (nutzt certifi): feedparser/urllib scheitert mit dem
            # python.org-Python auf macOS an der Zertifikatspruefung -> still 0 Eintraege.
            resp = requests.get(rss_url, timeout=15, headers={"User-Agent": "llm-scout-lab/1.0"})
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)
            if feed.bozo and not feed.entries:
                print(f"  WARNUNG {rss_url}: Feed nicht lesbar ({feed.get('bozo_exception')})", file=sys.stderr)
            print(f"  RSS {rss_url}: {len(feed.entries)} Einträge (cutoff: {cutoff_date.strftime('%Y-%m-%d')})")
            for entry in feed.entries:
                # Datum prüfen – updated_parsed ist time.struct_time (UTC)
                updated_parsed = getattr(entry, 'updated_parsed', None)
                if updated_parsed:
                    updated_dt = datetime(*updated_parsed[:6])
                    if updated_dt > cutoff_date:
                        items.append({
                            "source": "github",
                            "title": entry.title,
                            "url": entry.link,
                            "summary": entry.summary[:200] + "..." if len(entry.summary) > 200 else entry.summary
                        })
                else:
                    print(f"    (kein Datum) {entry.title}")
        except Exception as e:
            print(f"Fehler beim Abrufen von {rss_url}: {e}", file=sys.stderr)

    return items


def select_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Was tatsaechlich bewertet wird: Top 3 HF + Top 3 GitHub (Kontext sparen).
    Nur diese Items werden nach einem gespeicherten Bericht als verarbeitet markiert."""
    hf = [i for i in items if i['source'] == 'huggingface'][:3]
    gh = [i for i in items if i['source'] == 'github'][:3]
    return hf + gh


def router_ready(timeout: float = 5.0) -> bool:
    """Laeuft der llama-server? Ohne ihn gar nicht erst anfangen (nichts markieren)."""
    try:
        return requests.get(f"{LLAMA_SERVER_URL}/v1/models", timeout=timeout).status_code == 200
    except Exception:
        return False


def call_llm_for_evaluation(items: List[Dict[str, Any]]) -> str:
    """
    Sendet die Liste der neuen Items an llama-server zur Bewertung.
    """
    if not items:
        return "Keine neuen relevanten Entwicklungen gefunden."

    # Prompt Konstruktion
    system_prompt = """
    Du bist ein Experte für lokale LLM-Infrastruktur (llama.cpp, Ollama, GGUF).
    Deine Aufgabe ist es, eine Liste neuer Modell-Releases und Tool-Updates zu bewerten.

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

    ## Top Modelle
    - **[Modellname](Link)**: Kurze Begründung (Größe, Leistung, Sprache).

    ## Tool Updates
    - **[Toolname](Link)**: Wichtige neue Features.

    ## Fazit
    Ein Satz zusammenfassend, ob sich ein Update lohnt.
    """

    # Items für den Prompt vorbereiten (max 10 Items, um Kontext zu sparen)
    # Wir nehmen die Top 3 HF und Top 3 GH
    relevant_items = select_items(items)

    items_text = "\n".join([
        f"- Source: {i['source']}, Title: {i['title']}, URL: {i['url']}, Summary: {i['summary']}"
        for i in relevant_items
    ])

    user_prompt = f"""
    Hier sind die neuen Entwicklungen der letzten Woche:

    {items_text}

    Bitte bewerte diese und erstelle das Infopaper.
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


def main():
    # Exit-Code-Semantik:
    #   0 = Erfolg (inkl. "keine neuen Items")
    #   1 = kritischer Fehler (API-Abruf, LLM-Evaluation, DB-Fehler)
    #   2 = llama-server nicht erreichbar
    print("--- Local LLM Scout gestartet ---")

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
        hf_items = fetch_hf_trending()
        gh_items = fetch_github_releases()
        all_items = hf_items + gh_items
        print(f"Gesamt gefunden: {len(hf_items)} HF + {len(gh_items)} GH = {len(all_items)} Items")

        # 2. Filtern (nur neue) – noch NICHT markieren
        new_items = []
        for item in all_items:
            if is_new_item(conn, item['url']):
                new_items.append(item)
            else:
                print(f"  (bereits verarbeitet) {item['title']}")
        print(f"Neue Items: {len(new_items)}")

        if not new_items:
            conn.close()
            print("Keine neuen Items gefunden. Skript beendet.")
            sys.exit(0)

        print(f"Gefunden {len(new_items)} neue Items. Bewerte sie...")

        # 3. Evaluation durch LLM
        report_content = call_llm_for_evaluation(new_items)

        # 4. Bericht speichern (A1: Zweitlauf hängt nach, statt zu überschreiben)
        os.makedirs(REPORT_DIR, exist_ok=True)
        now = datetime.now()
        filename = week_key_for_filename(now)
        filepath = REPORT_DIR / filename

        save_report(filepath, report_content, now)
        print(f"Bericht gespeichert unter: {filepath}")

        # 5. Erst jetzt markieren – und nur, was wirklich bewertet wurde
        evaluated = select_items(new_items)
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
