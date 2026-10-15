#!/usr/bin/env python3
"""
LLM Scout E-Mail-Versand.

Liest den aktuellen KW-Bericht aus agents/llm_scout/data/weekly-reports/,
konvertiert Markdown zu HTML und versendet ihn per SMTP an Gmail.

Credentials werden aus dem macOS-Schlüsselbund geholt (service: lab-scout-smtp).

Exit-Code 0 bei Erfolg oder wenn keine KW-Datei existiert.
Exit-Code 1 bei Fehlern (Fehlermeldung in stderr).
"""

import os
import smtplib
import subprocess
import sys
from datetime import datetime
from email.mime.text import MIMEText
from pathlib import Path

import markdown

# --- KONFIGURATION ---

# Gleicher Mechanismus wie llm_scout.py: LAB_DIR aus Env oder Default
BASE_DIR = Path(os.getenv("LAB_DIR", Path.home() / "lab"))
REPORT_DIR = BASE_DIR / "weekly-reports"

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SENDER = "askvalentinai@gmail.com"
RECIPIENT = "askvalentinai@gmail.com"
KEYCHAIN_SERVICE = "lab-scout-smtp"


def get_password() -> str:
    """Holt das App-Passwort aus dem macOS-Schlüsselbund."""
    try:
        password = subprocess.check_output(
            ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"],
            stderr=subprocess.PIPE,
        ).decode().strip()
        if not password:
            raise RuntimeError("Schlüsselbund-Eintrag ist leer")
        return password
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Schlüsselbund-Eintrag '{KEYCHAIN_SERVICE}' nicht gefunden "
            f"(security exit code {e.returncode})"
        ) from e


def find_current_report() -> Path | None:
    """
    Sucht die Bericht-Datei der aktuellen Kalenderwoche.
    Gibt None zurück, wenn keine vorhanden ist.
    """
    iso_cal = datetime.now().isocalendar()
    kw = iso_cal[0]  # Jahr
    week = iso_cal[1]  # Kalenderwoche
    filename = f"llm_scout_kw{week}_{kw}.md"
    filepath = REPORT_DIR / filename
    if filepath.exists():
        return filepath
    return None


def send_email(report_path: Path) -> None:
    """Konvertiert Markdown zu HTML und versendet per SMTP."""
    iso_cal = datetime.now().isocalendar()
    kw_year = iso_cal[0]
    week = iso_cal[1]
    subject = f"LLM Scout KW{week} {kw_year}"

    # Markdown lesen und zu HTML konvertieren
    md_content = report_path.read_text(encoding="utf-8")
    html_body = markdown.markdown(
        md_content,
        extensions=["extra", "tables", "fenced_code"],
    )

    # HTML-E-Mail zusammenbauen (mit minimalem CSS fuer bessere Lesbarkeit)
    html_template = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; color: #333; max-width: 700px; margin: 0 auto; padding: 20px; }}
code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }}
pre {{ background: #f4f4f4; padding: 12px; border-radius: 5px; overflow-x: auto; }}
pre code {{ background: none; padding: 0; }}
h1, h2, h3 {{ color: #222; }}
a {{ color: #1a73e8; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
th {{ background: #f0f0f0; }}
</style>
</head>
<body>
{html_body}
<hr>
<p style="font-size: 0.85em; color: #888;">
Automatisch generiert vom LLM Scout (llama-server Lab).
</p>
</body>
</html>"""

    msg = MIMEText(html_template, "html", "utf-8")
    msg["Subject"] = subject
    msg["From"] = SENDER
    msg["To"] = RECIPIENT

    password = get_password()

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SENDER, password)
        server.sendmail(SENDER, [RECIPIENT], msg.as_string())


def main():
    # 1. Bericht-Datei finden
    report_path = find_current_report()
    if report_path is None:
        print("Keine Bericht-Datei fuer die aktuelle KW gefunden. Kein Versand.", file=sys.stderr)
        sys.exit(0)

    print(f"Bericht gefunden: {report_path}")

    try:
        send_email(report_path)
        print(f"E-Mail versendet: {report_path.name}")
        sys.exit(0)
    except Exception as e:
        print(f"Fehler beim E-Mail-Versand: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
