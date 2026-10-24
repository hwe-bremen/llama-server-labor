#!/usr/bin/env python3
"""
Einliefern.py — Lädt alle .eml-Dateien aus dem Verzeichnis mails/
in einen GreenMail-IMAP-Server ein.

Nutzung:
    python einliefern.py [--dir MAILDIR] [--host HOST] [--port PORT]

Standard:
    MAILDIR = ./mails (relativ zum Skript)
    HOST = 127.0.0.1
    PORT = 3025 (SMTP)
    IMAP_HOST = 127.0.0.1
    IMAP_PORT = 3143
    USER = testuser
    PASSWORD = testpass
"""

import argparse
import email
import os
import smtplib
import sys
from pathlib import Path


def deliver_maildir(mails_dir: Path, smtp_host: str, smtp_port: int,
                    imap_host: str, imap_port: int,
                    user: str, password: str) -> None:
    """Liest alle .eml-Dateien und sendet sie per SMTP an GreenMail."""
    eml_files = sorted(mails_dir.glob("*.eml"))
    if not eml_files:
        print(f"Keine .eml-Dateien in {mails_dir}")
        return

    print(f"Finde {len(eml_files)} .eml-Dateien in {mails_dir}")

    # SMTP-Verbindung aufbauen
    try:
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
        server.ehlo()
        server.starttls()
        server.login(user, password)
    except Exception as e:
        print(f"SMTP-Verbindung fehlgeschlagen: {e}", file=sys.stderr)
        sys.exit(1)

    delivered = 0
    for eml_file in eml_files:
        try:
            with open(eml_file, "r", encoding="utf-8") as f:
                msg = email.message_from_file(f)
            server.sendmail(
                msg["From"],
                msg["To"],
                msg.as_string(),
            )
            delivered += 1
            print(f"  Eingeliefert: {eml_file.name}")
        except Exception as e:
            print(f"  Fehler bei {eml_file.name}: {e}", file=sys.stderr)

    server.quit()
    print(f"Erledigt: {delivered}/{len(eml_files)} Mails eingeliefert.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Liefern Testmails in GreenMail ein")
    parser.add_argument(
        "--dir",
        type=Path,
        default=Path(__file__).parent / "mails",
        help="Verzeichnis mit .eml-Dateien",
    )
    parser.add_argument("--smtp-host", default="127.0.0.1", help="SMTP-Host")
    parser.add_argument("--smtp-port", type=int, default=3025, help="SMTP-Port")
    parser.add_argument("--imap-host", default="127.0.0.1", help="IMAP-Host")
    parser.add_argument("--imap-port", type=int, default=3143, help="IMAP-Port")
    parser.add_argument("--user", default="testuser", help="IMAP-Benutzer")
    parser.add_argument("--password", default="testpass", help="IMAP-Passwort")
    args = parser.parse_args()

    if not args.dir.exists():
        print(f"Verzeichnis existiert nicht: {args.dir}", file=sys.stderr)
        sys.exit(1)

    deliver_maildir(
        mails_dir=args.dir,
        smtp_host=args.smtp_host,
        smtp_port=args.smtp_port,
        imap_host=args.imap_host,
        imap_port=args.imap_port,
        user=args.user,
        password=args.password,
    )


if __name__ == "__main__":
    main()
