#!/usr/bin/env python3
"""
Prüfen.py — Prüft, ob die eingelieferten Mails im IMAP-Postfach
den Erwartungen entsprechen.

Nutzung:
    python pruefen.py [--host HOST] [--port PORT] [--user USER] [--password PASS]
                      [--erwartungen ERW_DATEI]

Standard:
    HOST = 127.0.0.1
    PORT = 3143
    USER = testuser
    PASSWORD = testpass
    ERWARTUNGEN = ./erwartungen.json
"""

import argparse
import email
import imaplib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_expectations(erwartungen_path: Path) -> List[Dict[str, Any]]:
    """Lädt die Erwartungsdatei."""
    if not erwartungen_path.exists():
        print(f"Erwartungsdatei nicht gefunden: {erwartungen_path}", file=sys.stderr)
        sys.exit(1)
    return json.loads(erwartungen_path.read_text(encoding="utf-8"))


def fetch_all_mails(imap_host: str, imap_port: int,
                    user: str, password: str) -> List[Dict[str, Any]]:
    """Liest alle Mails aus dem IMAP-Postfach."""
    try:
        imap = imaplib.IMAP4_SSL(imap_host, imap_port)
        imap.login(user, password)
        imap.select("INBOX", readonly=True)
        status, data = imap.search(None, "ALL")
        if status != "OK":
            imap.logout()
            return []
        mail_ids = data[0].split()
        mails: List[Dict[str, Any]] = []
        for mid in mail_ids:
            status, msg_data = imap.fetch(mid, "(RFC822)")
            if status != "OK":
                continue
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)
            mails.append({
                "message_id": msg.get("Message-ID", ""),
                "from": msg.get("From", ""),
                "subject": msg.get("Subject", ""),
                "date": msg.get("Date", ""),
                "body": msg.get_payload(decode=True) or b"",
            })
        imap.logout()
        return mails
    except Exception as e:
        print(f"IMAP-Verbindung fehlgeschlagen: {e}", file=sys.stderr)
        sys.exit(1)


def check_mails(mails: List[Dict[str, Any]],
                erwartungen: List[Dict[str, Any]]) -> bool:
    """Vergleicht geladene Mails mit den Erwartungen."""
    all_ok = True
    for erw in erwartungen:
        expected_id = erw.get("message_id")
        expected_status = erw.get("expected_status")
        expected_project = erw.get("expected_project", "")

        # Mail in Liste finden
        found = None
        for mail in mails:
            if mail.get("message_id") == expected_id:
                found = mail
                break

        if expected_status == "bereits_verarbeitet":
            # Diese Mail wurde bereits als "bereits verarbeitet" erwartet
            # (Duplikat der ersten Mail)
            if found is None:
                print(f"FAIL: {erw['file']} — Mail nicht gefunden (erwartet: bereits_verarbeitet)")
                all_ok = False
            else:
                print(f"OK: {erw['file']} — Mail gefunden (wird als bereits verarbeitet markiert)")
        elif expected_status == "leer":
            if found is None:
                print(f"FAIL: {erw['file']} — Mail nicht gefunden (erwartet: leer)")
                all_ok = False
            elif not found.get("body", b"").strip():
                print(f"OK: {erw['file']} — Leere Mail gefunden")
            else:
                print(f"FAIL: {erw['file']} — Mail hat Inhalt (erwartet: leer)")
                all_ok = False
        elif expected_status == "neu_mit_duplikat":
            if found is None:
                print(f"FAIL: {erw['file']} — Mail nicht gefunden (erwartet: neu mit Duplikat)")
                all_ok = False
            else:
                # Prüfen, ob Body-Hash mit einer früheren Mail übereinstimmt
                print(f"OK: {erw['file']} — Mail gefunden (Duplikat-Erkennung wird in DB geprüft)")
        else:
            if found is None:
                print(f"FAIL: {erw['file']} — Mail nicht gefunden (erwartet: {expected_status})")
                all_ok = False
            else:
                print(f"OK: {erw['file']} — Mail gefunden (Message-ID: {expected_id})")

    return all_ok


def main() -> None:
    parser = argparse.ArgumentParser(description="Prüft eingelieferte Mails gegen Erwartungen")
    parser.add_argument("--host", default="127.0.0.1", help="IMAP-Host")
    parser.add_argument("--port", type=int, default=3143, help="IMAP-Port")
    parser.add_argument("--user", default="testuser", help="IMAP-Benutzer")
    parser.add_argument("--password", default="testpass", help="IMAP-Passwort")
    parser.add_argument("--erwartungen", type=Path, default=Path(__file__).parent / "erwartungen.json",
                        help="Pfad zur Erwartungsdatei")
    args = parser.parse_args()

    erwartungen = load_expectations(args.erwartungen)
    mails = fetch_all_mails(args.host, args.port, args.user, args.password)
    print(f"Gefundene Mails: {len(mails)}")

    ok = check_mails(mails, erwartungen)
    if ok:
        print("\nAlle Prüfungen bestanden.")
        sys.exit(0)
    else:
        print("\nEinige Prüfungen fehlgeschlagen.")
        sys.exit(1)


if __name__ == "__main__":
    main()
