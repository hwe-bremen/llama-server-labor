#!/usr/bin/env python3
"""pruefen.py — Strukturierte Pruefungen der Planungsdatei und DB.

Prueft die Planungsdatei (planung.md) und die SQLite-DB (mail_planung.db)
in MAIL_PLAN_DIR gegen erwartungen.json. Nutzt imaplib.IMAP4 (unverschluesselt).

Verwendung:
    python3 pruefen.py --plan-dir <MAIL_PLAN_DIR> --expectations <erwartungen.json>
"""

import argparse
import hashlib
import imaplib
import json
import re
import sqlite3
import sys
from pathlib import Path


def load_expectations(path: Path) -> dict:
    """Laedt erwartungen.json und validiert das Format."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Fehler: erwartungen.json nicht geladen: {e}", file=sys.stderr)
        sys.exit(1)


def parse_blocks(planung_path: Path) -> list[dict]:
    """Parst die Planungsdatei in einzelne Blöcke."""
    if not planung_path.exists():
        return []

    content = planung_path.read_text(encoding="utf-8")
    blocks = []

    # Block-Grenzen: ## <Datum> — <Betreff>
    pattern = re.compile(
        r"## (\d{4}-\d{2}-\d{2})\s*—\s*(.+?)(?=\n## |\Z)",
        re.DOTALL,
    )

    for match in pattern.finditer(content):
        date_str = match.group(1)
        subject = match.group(2).strip()
        body = match.group(0)

        # Message-ID extrahieren
        mail_id_match = re.search(r"<!-- mail-id:\s*(.+?)\s*-->", body)
        message_id = mail_id_match.group(1).strip() if mail_id_match else None

        # Absender extrahieren
        from_match = re.search(r"> Absender:\s*(.+)", body)
        sender = from_match.group(1).strip() if from_match else None

        # Projekt extrahieren
        project_match = re.search(r"> Projekt:\s*(.+)", body)
        project = project_match.group(1).strip() if project_match else None

        blocks.append({
            "date": date_str,
            "subject": subject,
            "message_id": message_id,
            "sender": sender,
            "project": project,
            "body": body,
        })

    return blocks


def check_db(db_path: Path, message_id: str) -> bool:
    """Prueft, ob eine Message-ID in der DB markiert ist."""
    if not db_path.exists():
        return False
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM processed_mails WHERE message_id = ?", (message_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    except sqlite3.Error:
        return False


def count_db_rows(db_path: Path) -> int:
    """Zaehlt alle Zeilen in processed_mails."""
    if not db_path.exists():
        return 0
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM processed_mails")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except sqlite3.Error:
        return 0


def run_checks(plan_dir: Path, expectations: dict) -> list[str]:
    """Fuehrt alle strukturellen Pruefungen durch."""
    errors = []
    planung_path = plan_dir / "planung.md"
    db_path = plan_dir / "mail_planung.db"

    # Planungsdatei muss existieren
    if not planung_path.exists():
        errors.append("Planungsdatei fehlt")
        return errors

    # DB muss existieren
    if not db_path.exists():
        errors.append("DB fehlt")
        return errors

    blocks = parse_blocks(planung_path)

    # Pro Mail-Block: existiert oder nicht
    for mail_num, expected in expectations.items():
        msg_id = expected.get("message_id")
        block_exists_expected = expected.get("block_exists", True)

        # Block suchen
        matching_blocks = [b for b in blocks if b["message_id"] == msg_id]

        if block_exists_expected and not matching_blocks:
            errors.append(f"Mail {mail_num}: Block fehlt (erwartet message_id={msg_id})")
            continue

        if not block_exists_expected and matching_blocks:
            errors.append(f"Mail {mail_num}: Block existiert (erwartet nicht vorhanden)")
            continue

        if matching_blocks:
            block = matching_blocks[0]

            # Giftmail: "Auswertung fehlgeschlagen"
            if expected.get("has_error_warning"):
                if "> ⚠ Auswertung fehlgeschlagen" not in block["body"]:
                    errors.append(f"Mail {mail_num}: Fehlerwarnung fehlt")

            # Kein verwertbarer Inhalt
            if expected.get("has_kein_inhalt"):
                if "> Kein verwertbarer Inhalt" not in block["body"]:
                    errors.append(f"Mail {mail_num}: 'Kein verwertbarer Inhalt' fehlt")

            # Duplikat-Warnung
            if expected.get("has_duplikat_warning"):
                if "⚠️ mögliches Duplikat von" not in block["body"]:
                    errors.append(f"Mail {mail_num}: Duplikat-Warnung fehlt")

            # Kuerzungshinweis
            if expected.get("has_kuerzungshinweis"):
                if "> (Mailtext für die Auswertung gekürzt)" not in block["body"]:
                    errors.append(f"Mail {mail_num}: Kuerzungshinweis fehlt")

            # Aufgaben-Kategorie
            if expected.get("has_aufgaben"):
                if "### Aufgaben" not in block["body"]:
                    errors.append(f"Mail {mail_num}: Aufgaben-Kategorie fehlt")

            # Projekt
            expected_project = expected.get("project")
            if expected_project and block.get("project") != expected_project:
                errors.append(
                    f"Mail {mail_num}: Projekt '{block.get('project')}' != '{expected_project}'"
                )

            # Umlaute korrekt (Mail 05)
            if mail_num == "05":
                if "ä" not in planung_path.read_text(encoding="utf-8"):
                    errors.append("Mail 05: Umlaute nicht korrekt (UTF-8)")

            # DB-Marker
            if msg_id and not check_db(db_path, msg_id):
                errors.append(f"Mail {mail_num}: DB-Marker fehlt fuer {msg_id}")

    return errors


def check_byte_identity(first_path: Path, second_path: Path) -> bool:
    """Prueft, ob zwei Dateien byte-identisch sind."""
    if not first_path.exists() or not second_path.exists():
        return False
    return first_path.read_bytes() == second_path.read_bytes()


def main():
    parser = argparse.ArgumentParser(description="Pruefskript fuer mail_planung")
    parser.add_argument("--plan-dir", required=True, help="Pfad zu MAIL_PLAN_DIR")
    parser.add_argument("--expectations", required=True, help="Pfad zu erwartungen.json")
    parser.add_argument("--first-run-plan", required=True, help="Pfad zur Planungsdatei nach erstem Lauf (Byte-Identitaets-Prüfung)")
    args = parser.parse_args()

    plan_dir = Path(args.plan_dir)
    expectations = load_expectations(Path(args.expectations))

    errors = run_checks(plan_dir, expectations)

    # Byte-Identitaets-Prüfung (zweiter Lauf)
    if args.first_run_plan:
        first_path = Path(args.first_run_plan)
        second_path = plan_dir / "planung.md"
        if not check_byte_identity(first_path, second_path):
            errors.append("Planungsdatei nach zweitem Lauf nicht byte-identisch")

    if errors:
        print("Pruefungen fehlgeschlagen:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)

    print("Alle Pruefungen bestanden.")
    sys.exit(0)


if __name__ == "__main__":
    main()
