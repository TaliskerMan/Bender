# Bender

> *"Bite my shiny metal app!"*

**Bender** is a GTK4 + libadwaita Linux workstation dashboard for GNOME. Named after everyone's favourite bending unit from Futurama, it wraps common daily Linux sysadmin tasks into a polished tabbed GUI so you don't have to remember 69 bash commands.

## Features

| Tab | What it does |
|---|---|
| 🖥 **System Overview** | Hostname, disk usage, memory, uptime, displays, top processes (auto-refresh) |
| 🔐 **Security Audit** | UID-0 users, 777-permission files, SUID/SGID, zombie processes, login audit, hidden processes |
| 🌐 **Network Monitor** | Live connections, port checker, DNS lookup, whois, DNS flush, DDoS connection counts |
| 🛠 **Maintenance** | System update, Flatpak update, clear shared memory, clean logs, temp cleanup, GNOME reset |
| 🌤 **Weather** | 3-day forecast via wttr.in — no ansiweather required. °F/°C toggle |
| 🔒 **Proxy Manager** | Tinyproxy start/stop, blocklist editor, Steven Black auto-update, live log tail |

## Requirements

```
python3-gi  gir1.2-gtk-4.0  gir1.2-adw-1  policykit-1  hicolor-icon-theme
```

## Run from Source

```bash
git clone https://github.com/TaliskerMan/Bender.git
cd Bender
bash run.sh
```

## Install from .deb

```bash
sudo dpkg -i artifacts/bender_*_all.deb
```

## Build the .deb Package

```bash
cd Bender
dpkg-buildpackage -us -uc -b
```

## Author

Chuck Talk — [GitHub](https://github.com/TaliskerMan) · GPLv3
