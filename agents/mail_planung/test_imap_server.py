#!/usr/bin/env python3
"""
Test-IMAP-Server — Fundstelle f�r einen lokalen IMAP-Testserver.

Die Spec (spec_20261022_mail_planung.md, Offene Fragen 1) legt fest:
  "Tests ohne echten Server, Mail-Zugriff im Test ersetzt. Einen echten
   Testserver nur mit Fundstelle nennen, sonst offener Punkt."

Daher wird in tests/test_mail_planung.py der IMAP-Zugriff per Mock ersetzt.
Dieses Modul dient als Fundstelle f�r eine sp�tere Umsetzung eines echten
Test-IMAP-Servers.

M�gliche Umsetzungen:
- Minimaler Server per threading + socket (imaplib-kompatibel)
- Externes Werkzeug wie pyimap oder aiosmtpd (IMAP-Erweiterung)
- Dovecot-Stub

Anforderungen an einen echten Testserver:
- MIME-Parsing (text/plain, text/html, multipart)
- Umlaute (UTF-8)
- Anhang (application/*, ignoriert vom Werkzeug)
- FLAGS-Abfrage (\\Seen, \\Deleted)
- Read-only Modus (select(readonly=True))
- Message-ID-Header
"""

# Platzhalter — kein funktionierender Server in dieser Version.
# Tests verwenden stattdessen unittest.mock.patch auf fetch_mails().

__all__ = []  # Kein Export — nur Fundstelle
