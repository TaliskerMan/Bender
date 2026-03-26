# Bender v0.1.0-1

Initial official release of **Bender**, the shiny metal Linux workstation dashboard!

## Features included:
*   🖥 **System Overview:** Hostname, disk usage, memory, uptime, displays, top processes
*   🔐 **Security Audit:** UID-0 users, 777-permission files, SUID/SGID, login audit, hidden processes
*   🌐 **Network Monitor:** Live connections, port checker, DNS lookup, whois, DNS flush, DDoS connection counts
*   🛠 **Maintenance:** System update, Flatpak update, clear shared memory, clean logs, temp cleanup, GNOME reset
*   🌤 **Weather:** 5-day forecast wrapped natively using `ansiweather`
*   🔒 **Proxy Manager:** Tinyproxy start/stop, blocklist editor, Steven Black auto-update, live log tail

## Installation
```bash
sudo dpkg -i bender_0.1.0-1_all.deb
```
*(Optionally, verify the signature against the `.asc` and `.sha512` files before installing).*
