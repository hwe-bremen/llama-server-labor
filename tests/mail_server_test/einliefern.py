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
                    user: str, password: str, rcpt: str) -> None:
    """Liest alle .eml-Dateien und sendet sie per SMTP an GreenMail."""
    eml_files = sorted(mails_dir.glob("*.eml"))
    if not eml_files:
        print(f"Keine .eml-Dateien in {mails_dir}")
        return

    print(f"Finde {len(eml_files)} .eml-Dateien in {mails_dir}")

    # SMTP-Verbindung aufbauen (unverschlüsselt, ohne STARTTLS)
    try:
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
        server.ehlo()
    except Exception as e:
        print(f"SMTP-Verbindung fehlgeschlagen: {e}", file=sys.stderr)
        sys.exit(1)

    delivered = 0
    for eml_file in eml_files:
        try:
            raw = eml_file.read_bytes()  # Bytes senden: Umlaute ueberstehen smtplib nur so
            msg = email.message_from_bytes(raw)
            # Umschlag-Empfaenger immer das Testpostfach (Header-To bleibt unveraendert)
            server.sendmail(
                msg["From"] or "absender@lab.local",
                [rcpt],
                raw,
            )
            delivered += 1
            print(f"  Eingeliefert: {eml_file.name}")
        except Exception as e:
            print(f"  Fehler bei {eml_file.name}: {e}", file=sys.stderr)

    server.quit()
    print(f"Erledigt: {delivered}/{len(eml_files)} Mails eingeliefert.")
    if delivered != len(eml_files):
        print("Nicht alle Mails eingeliefert -- Abbruch.", file=sys.stderr)
        sys.exit(1)


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
    parser.add_argument("--rcpt", default="testuser@lab.local", help="Umschlag-Empfaenger (Testpostfach)")
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
        rcpt=args.rcpt,
    )


if __name__ == "__main__":
    main()
