# Runbook – OpenCode im M4-Repo vom Mini aus (SSH über Tailscale)

Stand 15.10.2026. Ziel: Im Büro `opencode` **auf dem M4** starten, damit Dateien, Tests,
launchd, Schlüsselbund und Logs im einen echten Repo liegen (kein Mini-Klon mehr).

## Warum nicht „Tailscale SSH"?

Tailscale SSH (Anmeldung über das Tailnet statt über Schlüssel) kann auf macOS nur die
Open-Source-Variante `tailscaled` als **Server** – die App (Store/Standalone), die auf dem M4
läuft, nicht. Quelle: tailscale.com/kb/1065/macos-variants (Tabelle „Can be a Tailscale SSH
server": App Store no, Standalone no, tailscaled yes).
→ Wir nehmen das **eingebaute macOS-SSH** („Entfernte Anmeldung"), nur mit Schlüssel,
und begrenzen den Zugriff im Tailnet per ACL auf den Mini.

## 1. M4: Entfernte Anmeldung einschalten

Systemeinstellungen → Allgemein → Teilen → **Entfernte Anmeldung** an →
„Zugriff erlauben für: **Nur diese Benutzer**" → nur `hans-wernereberhardt`.
„Vollen Festplattenzugriff für entfernte Benutzer" **aus** lassen.

## 2. Mini: Schlüssel erzeugen und auf den M4 bringen

```bash
ssh-keygen -t ed25519 -C "mini->m4 lab" -f ~/.ssh/id_ed25519_m4     # Passphrase empfohlen
tailscale status | grep -i macbook                                   # Name/IP des M4 notieren
ssh-copy-id -i ~/.ssh/id_ed25519_m4.pub hans-wernereberhardt@<m4-name>   # einmal mit Passwort
```

`~/.ssh/config` auf dem Mini:
```
Host m4
    HostName <m4-name>            # MagicDNS-Name aus tailscale status, z.B. macbook-pro-von-hans-werner
    User hans-wernereberhardt
    IdentityFile ~/.ssh/id_ed25519_m4
    IdentitiesOnly yes
    ServerAliveInterval 30
```
Test: `ssh m4 hostname` → Name des M4, **ohne** Passwortabfrage.

## 3. M4: Passwort-Anmeldung abschalten (erst nach erfolgreichem Test in 2!)

```bash
sudo tee /etc/ssh/sshd_config.d/100-lab.conf >/dev/null <<'CONF'
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin no
CONF
sudo sshd -T | grep -iE "passwordauthentication|kbdinteractive|permitroot"   # alle "no"
```
Ungeprüft: dass macOS `sshd_config.d/` einliest – die `sshd -T`-Zeile zeigt es. Steht dort
noch `yes`, die drei Zeilen direkt in `/etc/ssh/sshd_config` eintragen.
Wirkung: Ein Gerät im Heimnetz kommt ohne Schlüssel nicht rein, auch wenn Port 22 dort offen ist.

## 4. Tailnet-ACL: nur der Mini darf auf Port 22

Admin-Konsole → Access controls. **Vorsicht:** Solange die Owner-Regel `*:*` drin ist, wirkt
die neue Regel nicht (alles ist ohnehin erlaubt). Ersetzt man sie, müssen iPad/iPhone/Mini
weiter auf 443 (Serve) kommen – sonst ist die Web-UI weg. Gerätenamen/IPs aus `tailscale status`.

```jsonc
{
  "hosts": {
    "m4":     "100.x.x.x",   // MacBook Pro M4
    "mini":   "100.x.x.x",   // Mac mini M2 (Büro)
    "ipad":   "100.x.x.x",
    "iphone": "100.x.x.x"
  },
  "acls": [
    // Web-UI / Proxys über Tailscale Serve
    {"action": "accept", "src": ["mini", "ipad", "iphone"], "dst": ["m4:443"]},
    // SSH nur vom Mini
    {"action": "accept", "src": ["mini"], "dst": ["m4:22"]}
    // weitere bewusst nötige Regeln hier ergänzen – alles andere ist dann zu
  ]
}
```
Erst speichern, dann prüfen: iPad → `.ts.net` lädt? Mini → `ssh m4 hostname` geht?
iPad → Port 22 geht **nicht** (z.B. mit einer SSH-App testen). Notfall: alte Regel wieder einsetzen.

## 5. Alltag im Büro

```bash
ssh m4
cd ~/PycharmProjects/llama-server
opencode                       # Provider wie am M4: 127.0.0.1:8091 bzw. :8092 (dort lokal!)
```
Auf dem M4 gilt dessen `~/.config/opencode/opencode.jsonc` (mit `"subagent": false`).
Der M4 muss wach sein (Büro-Launcher mit `caffeinate`). Abbruch der Verbindung beendet
OpenCode – für lange Läufe optional `tmux` (`brew install tmux`, dann `tmux new -s oc`).

## Sicherheits-Notizen

- Ein Schlüssel nur für diesen Zweck (`id_ed25519_m4`), mit Passphrase; widerrufbar durch
  Löschen der Zeile in `~/.ssh/authorized_keys` auf dem M4.
- SSH gibt eine **volle Shell** als dein Benutzer – mehr als der MCP-Server. Darum: nur Schlüssel,
  nur der Mini (ACL), kein Root.
- Der Mini-Klon `llama-server-labor` wird überflüssig; vorher prüfen, dass nichts Ungepushtes drinliegt.
