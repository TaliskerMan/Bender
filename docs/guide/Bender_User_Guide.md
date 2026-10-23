title: Bender
subtitle: Installation and User Guide
version: 0.1.14
platforms: Linux (GNOME)
## About Bender

Bender is a workstation dashboard for the Linux desktop. It gathers everyday administration tasks (checking the system, running quick security checks, network lookups, updates and clean-up, a weather forecast and a Tinyproxy ad-blocking proxy) into one window, so you don't have to remember the commands behind them.

> *"Bite my shiny metal app!"* Bender is named after the bending unit from *Futurama*.

**How it works.** Every panel runs standard Linux commands (such as `df`, `ss`, `dig`, `last` or `systemctl`) and shows their output. Anything that needs administrator rights asks for your password through the system's polkit dialog first. Output appears in the panel so you can read exactly what ran.

Bender is free, open-source software under the GNU General Public License v3. Source: github.com/TaliskerMan/Bender.

## System requirements

| | |
|---|---|
| Operating system | Debian, Ubuntu, Pop!_OS or a derivative |
| Desktop | GNOME, or any desktop with GTK 4 and Libadwaita |
| Required (installed with the package) | `python3-gi`, GTK 4 and Libadwaita bindings, `pkexec` (or `policykit-1`), `hicolor-icon-theme`, `iproute2`, `procps` |
| Recommended (for individual features) | `dnsutils` (DNS lookup), `whois`, `unhide` (hidden processes), `flatpak`, `tinyproxy` (Proxy panel), `ansiweather` (Weather panel) |
| Suggested | `nala` (System Update uses it when installed, otherwise `apt-get`) |
| Also used if present | `xrandr` (display list) |

Panels whose tool is missing tell you so instead of failing silently.

## Installing Bender

### From the release package

Each release includes `bender_<version>_all.deb`, a SHA-512 checksum, detached GPG signatures and the Nordheim Online public key (`chuck_pubkey.asc`).

```
sha512sum -c bender_0.1.14_all.deb.sha512
gpg --import chuck_pubkey.asc
gpg --verify bender_0.1.14_all.deb.asc bender_0.1.14_all.deb
sudo apt install ./bender_0.1.14_all.deb
```

`apt` installs the required packages and offers the recommended ones. To get every feature at once:

```
sudo apt install dnsutils whois unhide flatpak tinyproxy ansiweather nala
```

Open **Bender** from your applications menu or run `bender`.

### From source

```
git clone https://github.com/TaliskerMan/Bender.git
cd Bender
bash run.sh
```

### Uninstalling

`sudo apt remove bender`.

## Getting around

Bender's window has a sidebar with eight panels: **System**, **Security**, **Network**, **Connections**, **Maintenance**, **Weather**, **Proxy** and **About**. Click a panel name to open it. Panels that run checks show their output in a text area you can scroll and copy from; a **Clear** button empties it.

> **Note:** When a task needs administrator rights, your desktop shows a password dialog from polkit. Bender never stores your password.

## System

A live overview of the computer, refreshed automatically every 15 seconds (or click **Refresh All**):

| Section | Command behind it |
|---|---|
| System Info | `hostnamectl` |
| Disk Usage | `df -hlT` (local disks, excluding temporary filesystems) |
| Memory | `free -h` |
| Uptime & Load | `uptime -p` and `/proc/loadavg` |
| Connected Displays | `xrandr` (may show "not available" on Wayland) |
| Top 10 Processes | `ps`, sorted by memory use |

## Security

Quick checks you can run one at a time with **Run**, or all together with **Run All Checks**. Results appear in the panel's output area, and each check shows a badge: ✅ nothing of concern found, ⚠️ something to review, ℹ️ information only (no pass or fail), ❌ the check couldn't run.

| Check | What it looks for | Badge | Admin rights |
|---|---|---|---|
| UID-0 & Sudo Users | Accounts with root's user ID, and members of the sudo group | ⚠️ if any account other than root has user ID 0 | No |
| World-Writable Files (folders you can read) | Files anyone can change (first 50, on the root filesystem). Folders you can't read are skipped | ⚠️ if any are found | No |
| SUID / SGID Files | Programs in system folders that run with elevated rights | ℹ️ | No |
| Accounts with a Login Shell | Every account that can log in with a shell | ℹ️ | No |
| Zombie Processes | Processes that ended but weren't cleaned up | ⚠️ if any are found | No |
| Recent Login Audit | The last 20 logins (`last`) | ℹ️ | No |
| Hidden Processes (unhide) | Processes hidden from normal tools, a rootkit sign | ⚠️ if unhide reports one | Yes; needs `unhide` |

These checks report; they don't change anything. Treat unexpected results as a prompt to investigate, not proof of a problem.

## Network and Connections

### Network

| Tool | What it does | Admin rights |
|---|---|---|
| Port Checker | Shows whether anything is listening on a TCP port you enter (`ss`). Program names are shown for your own programs; for system services you see the socket but not the name | No |
| DNS Lookup (dig) | Looks up a domain's DNS records | No |
| Whois | Shows a domain's registration details | No |
| DNS Cache Flush | Clears the local DNS cache (`resolvectl flush-caches`) | Yes |
| Connections per IP (DDoS Indicator) | Counts current connections by remote address, so unusual floods stand out | No |

Domain names and port numbers are checked before they're used, so a typed value can't be run as a command or passed as an option.

### Connections

Lists every active network connection and listening socket (`ss -tunap`). Click **Refresh** to update. Process names for other users' connections only appear when you run Bender with more privileges.

## Maintenance

Each action has a **Run** button and a one-line description. **Every action asks you to confirm before it runs**, and its output appears in **Global Output**, ending with whether it finished, failed, or was cancelled at the password prompt.

| Action | What it does | Admin rights |
|---|---|---|
| System Update | Updates package lists and upgrades all packages, with `nala` if it's installed, otherwise `apt-get`. Runs without asking questions and keeps your version of any config file you have changed | Yes |
| Flatpak Update | Updates your Flatpak apps, then system-wide Flatpaks if there are any | Only for system Flatpaks |
| Clean Shared Memory (/dev/shm) | Deletes **your own** files in `/dev/shm` that haven't changed for a day and that no running program has open or mapped | No |
| Clean Rotated Logs (.gz) | Deletes every compressed `.gz` log archive under `/var/log` | Yes |
| Clean Temp Files (/tmp) | Deletes **your own** `qipc*` and `gdm*` files in `/tmp` that haven't changed for a day and that no running program has open | No |
| Reset GNOME App Grid | Resets the app-grid layout, then **logs you out** to apply it | No |

> **Note:** The two updates can take several minutes and have no time limit, because stopping an upgrade part-way can leave packages half-installed. Their output appears when they finish.

> **Warning:** Deleted files can't be recovered. **Clean Rotated Logs** removes old system logs you may want for troubleshooting. The shared-memory and temp clean-ups never touch other users' or the system's files, or anything in use.

## Weather

Type a location (for example `Austin,TX,USA`), choose **°F (Imperial)** or **°C (Metric)**, and click **Get Weather**. Bender shows a multi-day forecast. Nothing is fetched until you click **Get Weather** (or change the unit after entering a location).

The forecast comes from the `ansiweather` tool, which fetches data from the OpenWeatherMap service over the internet; the location you enter is sent to that service. Bender remembers the last location and unit in `~/.config/bender/weather.json` (readable only by you) so the field is filled in next time. If `ansiweather` isn't installed, the panel says so.

## Proxy (Tinyproxy ad blocking)

The Proxy panel manages **Tinyproxy**, a small local web proxy, and its blocklist. Point your browser at the proxy to block ad and tracking domains. The panel needs the `tinyproxy` package; if it's missing, the panel says so.

> **Important:** Tinyproxy ships with filtering switched **off**, and while it is off the blocklist has no effect. The panel shows a warning when that's the case. To turn filtering on, add `Filter "/etc/tinyproxy/filter"` to `/etc/tinyproxy/tinyproxy.conf` (as administrator) and restart the proxy. If the config already names a different filter file, Bender edits that file.

| Control | What it does | Admin rights |
|---|---|---|
| Proxy Status | Shows whether Tinyproxy is running | No |
| Start Proxy / Stop Proxy | Starts or stops the `tinyproxy` service | Yes |
| Blocklist → Load / Save | Shows and edits the blocklist. Save applies it straight away if the proxy is running. If the file can't be read, Save is turned off so the real list can't be overwritten | Save: yes |
| Quick Add | Adds one domain to the blocklist | Yes |
| Auto-Update (Steven Black) | Downloads the Steven Black unified hosts list over HTTPS from GitHub (50 MB limit). You choose **Merge** (keep your list and add the new domains) or **Replace** (your current list, including domains you added, is removed) | Yes |
| Show Last 50 Lines | Shows the end of `/var/log/tinyproxy/tinyproxy.log`. On Debian and Ubuntu it's readable by members of the `adm` group | No |

Saving, Quick Add and Auto-Update ask for your password once, and restart Tinyproxy only if it's already running; they never start a proxy you have stopped. Only programs set to use the proxy are filtered: by default Tinyproxy listens on `127.0.0.1` port 8888 (the panel shows the port from your config). Tinyproxy treats each blocklist line as a pattern that can match part of a name, so a short entry can block more sites than you expect.

## Privacy and security

- Bender has no telemetry, account or cloud service.
- It uses the network only when you ask: DNS and whois lookups, weather, updates and the Steven Black list download. The weather location goes to OpenWeatherMap.
- Privileged commands run through polkit (`pkexec`) with fixed argument lists; typed values such as domains and ports are validated first.
- Bender stores no passwords.

## Troubleshooting

**A panel says a tool isn't installed.** Install the package named in the message, for example `sudo apt install ansiweather`.

**System Update fails.** Read the end of the output. "Cancelled" means the password prompt was closed. If another program is installing software, wait for it to finish and try again.

**Connected Displays says "xrandr not available".** That's expected on some Wayland sessions; use your desktop's display settings instead.

**Hidden Processes does nothing.** Install `unhide` and approve the password prompt.

**The blocklist has no effect.** Make sure your browser uses the proxy and that filtering is enabled in `/etc/tinyproxy/tinyproxy.conf` (the Proxy panel warns you if it isn't), then restart Tinyproxy.

**Save Blocklist is greyed out.** Bender couldn't read the blocklist file, so it won't risk overwriting it. The status line says why.

**The Port Checker shows a socket but no program name.** The program belongs to another user, usually a system service. The port is in use either way.

**I clicked Reset GNOME App Grid and was logged out.** That's how the reset is applied. Log back in; your app grid is back to the default layout.

## Support and license

Bender is free, open-source software. Report problems on GitHub (github.com/TaliskerMan/Bender) or email **chuck@nordheim.online**.

| | |
|---|---|
| Website | nordheim.online |
| Source code | github.com/TaliskerMan/Bender |
| License | GNU GPL v3 (no warranty) |
| Copyright | © 2026 Chuck Talk, Nordheim Online, LLC |
