#!/usr/bin/env python3
"""
LLM Scout E-Mail-Versand.

Liest den aktuellen KW-Bericht aus agents/llm_scout/data/weekly-reports/,
konvertiert Markdown zu HTML und versendet ihn per SMTP an Gmail.

Credentials werden aus dem macOS-Schlüsselbund geholt (service: lab-scout-smtp).

Exit-Code 0 bei Erfolg oder wenn keine KW-Datei existiert.
Exit-Code 1 bei Fehlern (Fehlermeldung in stderr).

Modi:
  - Normal (Default): Bericht finden, bauen, per SMTP versenden.
  - --dry-run: Bericht finden, bauen, als .eml in outbox/ ablegen (kein SMTP).
  - --fail-mail --exit-code <n>: Fehler-Mail bauen und versenden (mit Datei-Fallback).
"""

import argparse
import os
import smtplib
import subprocess
import sys
import tempfile
from datetime import datetime
from email.mime.text import MIMEText
from pathlib import Path

# import markdown: lazy in build_email_message() (N6)

# Gemeinsame Funktion fuer den Wochenschluessel (A7)
# send_scout_email.py liegt in scripts/, week_key.py in agents/llm_scout/
# Wir importieren ueber den relativen Modul-Pfad.
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent / "agents" / "llm_scout"))
from week_key import week_key_for_filename

# --- KONFIGURATION ---

# Gleicher Mechanismus wie llm_scout.py: LAB_DIR aus Env oder Default
BASE_DIR = Path(os.getenv("LAB_DIR", Path.home() / "lab"))
REPORT_DIR = BASE_DIR / "weekly-reports"
OUTBOX_DIR = BASE_DIR / "outbox"

# Versand-Nachweis: Zustandsdatei im REPORT_DIR (A1)
SENT_STATE_FILE = REPORT_DIR / ".sent_state"

# SMTP: Default Gmail, kann per Umgebungsvariablen überschrieben werden (Test-Support)
SMTP_HOST = os.getenv("SCOUT_SMTP_HOST", "smtp.gmail.com")
LOCAL_TEST_HOSTS = {"127.0.0.1", "localhost", "::1"}   # ohne SCOUT_ALLOW_SEND erlaubt
# SMTP_PORT wird lazy in send_email_smtp() geparst (N2: kein Crash beim Import)
SENDER = "askvalentinai@gmail.com"
RECIPIENT = "askvalentinai@gmail.com"
KEYCHAIN_SERVICE = "lab-scout-smtp"

# Exit-Code-Semantik des Scouts (für Fehler-Mail-Meldungen)
EXIT_CODE_MEANINGS = {
    2: "llama-server nicht erreichbar (kein Server unter der konfigurierten URL)",
    1: "Kritischer Fehler in der Scout-Pipeline (API-Abruf, LLM-Evaluation oder DB-Fehler) – Details im Log",
}


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
    Nutzt die gemeinsame Funktion week_key_for_filename() (A7).
    Gibt None zurueck, wenn keine vorhanden ist.
    """
    filename = week_key_for_filename(datetime.now())
    filepath = REPORT_DIR / filename
    if filepath.exists():
        return filepath
    return None


def build_email_message(report_path: Path) -> MIMEText:
    """
    Liest den Markdown-Bericht, konvertiert zu HTML und baut eine MIME-Message.
    Gibt die fertige MIMEText-Instanz zurück (ohne Versand).
    """
    iso_cal = datetime.now().isocalendar()
    kw_year = iso_cal[0]
    week = iso_cal[1]
    subject = f"LLM Scout KW{week} {kw_year}"

    # Markdown lesen und zu HTML konvertieren
    md_content = report_path.read_text(encoding="utf-8")
    # N6: lazy import – nur hier nötig, nicht in build_fail_email()
    import markdown as md_lib
    html_body = md_lib.markdown(
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
    return msg


def build_fail_email(exit_code: int) -> MIMEText:
    """
    Baut eine kurze Fehler-Mail basierend auf dem Scout-Exit-Code.
    """
    now = datetime.now()
    iso_cal = now.isocalendar()
    kw_year = iso_cal[0]
    week = iso_cal[1]
    date_str = now.strftime("%Y-%m-%d")
    timestamp_str = now.strftime("%Y-%m-%d %H:%M")

    # Ursache aus Mapping-Tabelle
    cause = EXIT_CODE_MEANINGS.get(exit_code, "Unbekannter Exit-Code – Details im Log")

    subject = f"LLM Scout FEHLER KW{week} {kw_year} – Exit-Code {exit_code}"

    html_body = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; color: #333; max-width: 700px; margin: 0 auto; padding: 20px; }}
</style>
</head>
<body>
<p>Die LLM-Scout-Pipeline vom {date_str} ist fehlgeschlagen.</p>
<p>Exit-Code: {exit_code}</p>
<p>Mögliche Ursache (nach Exit-Code-Semantik): {cause}</p>
<p></p>
<p>Details: logs/llm_scout_err.log (und llm_scout_out.log)</p>
<p>Letzter Scout-Aufruf: {timestamp_str}</p>
</body>
</html>"""

    msg = MIMEText(html_body, "html", "utf-8")
    msg["Subject"] = subject
    msg["From"] = SENDER
    msg["To"] = RECIPIENT
    return msg


def save_email_to_file(msg: MIMEText, filename: str) -> Path:
    """
    Speichert eine MIME-Message als .eml-Datei im outbox-Verzeichnis.
    Erstellt den outbox-Ordner bei Bedarf.
    """
    OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
    filepath = OUTBOX_DIR / filename
    filepath.write_text(msg.as_string(), encoding="utf-8")
    return filepath


def send_email_smtp(msg: MIMEText) -> None:
    """
    Versendet eine fertige MIME-Message per SMTP.
    Holt das Passwort aus dem Schlüsselbund.
    Port wird lazy geparst (vor Passwort, E4), damit ein ungültiger Port
    den Schlüsselbund nicht berührt.
    """
    # N2: Lazy-Port-Parsing; E4: vor get_password()
    try:
        smtp_port = int(os.getenv("SCOUT_SMTP_PORT", "587"))
    except (ValueError, TypeError) as port_err:
        raise ValueError(f"SCOUT_SMTP_PORT ist kein gueltiger Port: {os.getenv('SCOUT_SMTP_PORT', '')!r}") from port_err

    # Versand-Sperre (17.10.): Echte SMTP-Server nur mit SCOUT_ALLOW_SEND=1
    # (gesetzt in der launchd-plist und beim bewusst manuellen Versand).
    # Tests gegen 127.0.0.1/localhost bleiben ohne Variable moeglich.
    # Steht vor get_password(): gesperrt heisst auch kein Schluesselbund-Zugriff.
    if SMTP_HOST not in LOCAL_TEST_HOSTS and os.getenv("SCOUT_ALLOW_SEND") != "1":
        raise RuntimeError(
            f"Echter Versand an {SMTP_HOST} gesperrt (SCOUT_ALLOW_SEND=1 fehlt)"
        )

    password = get_password()

    with smtplib.SMTP(SMTP_HOST, smtp_port, timeout=30) as server:
        server.starttls()
        server.login(SENDER, password)
        server.sendmail(SENDER, [RECIPIENT], msg.as_string())


# --- MODI ---


# --- VERSEND-NACHWEIS (A1, A2, A6) ---

def get_current_week_key() -> str:
    """
    Liefert den Wochenschluessel fuer die aktuelle ISO-Kalenderwoche.
    Format: "YYYY_WW" (ISO-Jahr, ISO-KW), z. B. "2027_01".
    """
    iso_year, iso_week, _ = datetime.now().isocalendar()
    return f"{iso_year}_{iso_week:02d}"


def is_week_already_sent() -> bool:
    """
    Prueft, ob die aktuelle ISO-Kalenderwoche bereits im Versand-Nachweis steht.
    Gibt True zurueck, wenn eine Zeile mit dem aktuellen Wochenschluessel existiert.
    """
    if not SENT_STATE_FILE.exists():
        return False
    current_key = get_current_week_key()
    content = SENT_STATE_FILE.read_text(encoding="utf-8").strip()
    if not content:
        return False
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        # Zeilenformat: "YYYY_WW YYYY-MM-DD"
        parts = line.split()
        if parts and parts[0] == current_key:
            return True
    return False


def record_sent_week() -> None:
    """
    Speichert eine Zustandszeile fuer die aktuelle ISO-Kalenderwoche atomar.
    Format: "YYYY_WW YYYY-MM-DD" pro Zeile.
    Nutzt atomares Schreiben (Temp-Datei + os.replace) (A6).
    Wenn die Woche bereits im Nachweis steht, wird nichts geschrieben.
    """
    current_key = get_current_week_key()
    today = datetime.now().strftime("%Y-%m-%d")
    new_line = f"{current_key} {today}\n"

    # Pruefen, ob die Woche bereits im Nachweis steht
    if SENT_STATE_FILE.exists():
        content = SENT_STATE_FILE.read_text(encoding="utf-8").strip()
        for line in content.splitlines():
            line = line.strip()
            if line and line.split()[0] == current_key:
                # Bereits vorhanden, nichts tun
                return

    # Atomares Schreiben: zuerst in Temp-Datei, dann os.replace
    # Existierende Zeilen beibehalten
    existing_content = ""
    if SENT_STATE_FILE.exists():
        existing_content = SENT_STATE_FILE.read_text(encoding="utf-8")

    SENT_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Temp-Datei im gleichen Verzeichnis fuer atomares replace
    fd, tmp_path = tempfile.mkstemp(
        dir=str(SENT_STATE_FILE.parent),
        prefix=".sent_state_",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(existing_content)
            f.write(new_line)
        os.replace(tmp_path, str(SENT_STATE_FILE))
    except Exception:
        # Bei Fehler: Temp-Datei rueckstaendig loeschen
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise

def mode_normal() -> int:
    """
    Normaler Versand: Bericht finden, bauen, per SMTP versenden.

    Exit-Code 0: Erfolg oder KW bereits gesendet (A2).
    Exit-Code 1: SMTP-Fehler.
    Exit-Code 3: Bericht fehlt und Woche nicht abgedeckt (A3).
    """
    # A2: Pruefen, ob die KW bereits gesendet wurde
    if is_week_already_sent():
        print("KW bereits gesendet, kein Zweitversand.")
        return 0

    report_path = find_current_report()
    if report_path is None:
        # A3: Bericht fehlt und Woche nicht abgedeckt -> Exit 3
        print(
            "Fehler: Keine Bericht-Datei fuer die aktuelle KW gefunden, "
            "Woche noch nicht gesendet. Exit 3.",
            file=sys.stderr,
        )
        return 3

    print(f"Bericht gefunden: {report_path}")

    try:
        msg = build_email_message(report_path)
        send_email_smtp(msg)
        # A1: Nur nach erfolgreichem Versand den Nachweis schreiben
        record_sent_week()
        print(f"E-Mail versendet: {report_path.name}")
        return 0
    except Exception as e:
        print(f"Fehler beim E-Mail-Versand: {e}", file=sys.stderr)
        return 1


def mode_dry_run() -> int:
    """Trockenlauf: Bericht finden, bauen, als .eml ablegen (kein SMTP, kein Schlüsselbund)."""
    report_path = find_current_report()
    if report_path is None:
        print("Keine Bericht-Datei fuer die aktuelle KW gefunden. Kein Trockenlauf.", file=sys.stderr)
        return 0

    print(f"Bericht gefunden: {report_path}")

    try:
        msg = build_email_message(report_path)
        eml_filename = report_path.name.replace(".md", ".eml")
        saved = save_email_to_file(msg, eml_filename)
        print(f"Trockenlauf: E-Mail abgelegt unter {saved}")
        return 0
    except Exception as e:
        print(f"Fehler beim Bauen der E-Mail: {e}", file=sys.stderr)
        return 1


def mode_fail_mail(exit_code: int) -> int:
    """
    Fehler-Mail: Baut eine Fehler-Mail und versucht SMTP-Versand.
    Bei SMTP-Fehler: Datei-Fallback in outbox/.
    """
    try:
        msg = build_fail_email(exit_code)
    except Exception as e:
        print(f"Fehler beim Bauen der Fehler-Mail: {e}", file=sys.stderr)
        return 1

    # Versuch 1: SMTP-Versand
    try:
        send_email_smtp(msg)
        print(f"Fehler-Mail versendet (Exit-Code {exit_code})", file=sys.stderr)
        return 0
    except Exception as smtp_err:
        # Fallback: Datei ablegen (N4: sekunden-genau, E3: exklusiver Modus + Zaehler)
        try:
            now = datetime.now()
            base_name = f"scout_error_{now.strftime('%Y%m%d')}_{now.strftime('%H%M%S')}"
            eml_filename = f"{base_name}.eml"
            OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
            filepath = OUTBOX_DIR / eml_filename

            # E3: exklusiver Modus "x" verhindert Ueberschreibung;
            # bei FileExistsError Zaehler _1, _2 ... anhaengen
            counter = 0
            while True:
                try:
                    with open(filepath, "x", encoding="utf-8") as f:
                        f.write(msg.as_string())
                    break
                except FileExistsError:
                    counter += 1
                    filepath = OUTBOX_DIR / f"{base_name}_{counter}.eml"

            print(
                f"Fehler-Mail SMTP fehlgeschlagen ({smtp_err}), abgelegt unter {filepath}",
                file=sys.stderr,
            )
            return 0
        except Exception as file_err:
            print(
                f"Fehler-Mail: SMTP und Datei-Fallback fehlgeschlagen ({smtp_err}; {file_err})",
                file=sys.stderr,
            )
            return 1


def main():
    parser = argparse.ArgumentParser(
        description="LLM Scout E-Mail-Versand"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="E-Mail bauen und als .eml in outbox/ ablegen (kein SMTP, kein Schlüsselbund)",
    )
    parser.add_argument(
        "--fail-mail",
        action="store_true",
        help="Fehler-Mail bauen (benötigt --exit-code)",
    )
    parser.add_argument(
        "--exit-code",
        type=int,
        default=None,
        help="Exit-Code des Scouts für die Fehler-Mail",
    )

    args = parser.parse_args()

    if args.dry_run:
        if args.fail_mail:
            print(
                "Trockenlauf aktiv – Fehler-Mail-Versand uebersprungen.",
                file=sys.stderr,
            )
        exit_code = mode_dry_run()
    elif args.fail_mail:
        if args.exit_code is None:
            print("Fehler: --fail-mail erfordert --exit-code", file=sys.stderr)
            sys.exit(1)
        exit_code = mode_fail_mail(args.exit_code)
    else:
        exit_code = mode_normal()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
