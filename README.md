# Bender

> *"Bite my shiny metal app!"*

**Bender** is a GTK4 + libadwaita Linux workstation dashboard for GNOME. Named after everyone's favourite bending unit from Futurama, it wraps common daily Linux sysadmin tasks into a tabbed GUI, and shows you the output of every command it runs.

## Features

Bender has eight tabs:

| Tab | What it does |
|---|---|
| 🖥 **System** | Hostname, disk usage, memory, uptime and load, displays, top 10 processes by memory (refreshes every 15 s) |
| 🔐 **Security** | UID-0 and sudo users, world-writable files, SUID/SGID programs, accounts with a login shell, zombie processes, recent logins, hidden processes (`unhide`). Checks only report; they change nothing |
| 🌐 **Network** | Port checker (`ss`), DNS lookup (`dig`), whois, DNS cache flush, connections per remote address |
| 🔌 **Connections** | All current connections and listening sockets (`ss -tunap`) |
| 🛠 **Maintenance** | System update (nala if installed, otherwise apt-get), Flatpak update, shared-memory and temp-file clean-up, rotated-log clean-up, GNOME app-grid reset. **Every action asks before it runs** |
| 🌤 **Weather** | Multi-day forecast from the `ansiweather` tool (OpenWeatherMap data), °F/°C. Nothing is fetched until you click **Get Weather** |
| 🔒 **Proxy** | Tinyproxy start/stop, blocklist editor, Steven Black list update (merge or replace), last 50 log lines |
| ℹ️ **About** | Credits and the licence text |

### What the Maintenance actions do

- **System Update** upgrades every package without stopping to ask questions, and keeps your version of any config file you have changed. It has no time limit, because stopping an upgrade part-way can leave packages half-installed.
- **Clean Shared Memory** and **Clean Temp Files** delete only *your own* files (in `/dev/shm`, or `qipc*`/`gdm*` in `/tmp`) that haven't changed for a day and that no running program has open. Other users' and the system's files are never touched.
- **Clean Rotated Logs** permanently deletes the compressed old logs (`*.gz`) under `/var/log`.
- **Reset GNOME App Grid** logs you out to apply the reset.

### Privacy

Bender has no telemetry or account. It uses the network only when you ask it to: DNS and whois lookups, updates, the Steven Black list download, and the weather. The weather location you type is sent to OpenWeatherMap through `ansiweather`, and Bender remembers the last location in `~/.config/bender/weather.json`, readable only by you.

### Proxy blocklist: two things to know

Tinyproxy ships with filtering switched **off**, and while it is off the blocklist has no effect. The Proxy tab tells you when this is the case. To turn filtering on, add this line to `/etc/tinyproxy/tinyproxy.conf` and restart the proxy:

```
Filter "/etc/tinyproxy/filter"
```

Only programs set to use the proxy (by default `127.0.0.1`, port 8888) are filtered.

## Requirements

Installed automatically with the package:

```
python3-gi  gir1.2-gtk-4.0  gir1.2-adw-1  pkexec (or policykit-1)  hicolor-icon-theme  iproute2  procps
```

Recommended, for individual features: `dnsutils`, `whois`, `unhide`, `flatpak`, `tinyproxy`, `ansiweather`. Suggested: `nala`. A tab whose tool is missing tells you which package to install.

## Run from Source

To run Bender directly from the source without installing:

```bash
git clone https://github.com/TaliskerMan/Bender.git
cd Bender
bash run.sh
```

## Install from Release

Download the `.deb`, its `.sha512` and `.asc` files and the public key from the [Releases](https://github.com/TaliskerMan/Bender/releases) page, check them, then install:

```bash
sha512sum -c bender_<version>_all.deb.sha512
gpg --import chuck_pubkey.asc
gpg --verify bender_<version>_all.deb.asc bender_<version>_all.deb
sudo apt install ./bender_<version>_all.deb
```

## Build from Source Tarball / Repository

To build the Debian package and sign it:

```bash
# If using the source tarball, extract it first:
# tar -xzvf bender_source.tar.gz
cd Bender
bash build_release.sh
```

This places the `.deb`, its SHA-512 checksum and GPG signatures in the `artifacts/` folder. The build stops if a signature can't be made.

## Documentation

The full installation and user guide is [docs/Bender_User_Guide.pdf](docs/Bender_User_Guide.pdf) (source: [docs/guide/Bender_User_Guide.md](docs/guide/Bender_User_Guide.md)).

## Author

Chuck Talk — [GitHub](https://github.com/TaliskerMan) · GPLv3
