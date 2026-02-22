# PopICON Plan

## Goal
The goal of this script is to replace the `view-app-grid-symbolic.svg` icon in all installed icon themes with a customized Pop!_OS logo. This ensures consistent branding across the desktop environment's app grid button.

## Script Details
- **Script Name**: `replace_app_grid_icon.py`
- **Location**: This repository root.
- **Functionality**:
    1.  **Download**: Fetches the official Pop!_OS logo (256x256) from the `pop-os/icon-theme` GitHub repository.
    2.  **Process**: Modifies the SVG to make the circle white and the "P!" symbol transparent (using an SVG mask), creating a cutout effect.
    3.  **Locate**: Scans standard icon directories (`/usr/share/icons`, `~/.local/share/icons`, `~/.icons`) for `view-app-grid-symbolic.svg`.
    4.  **Backup**: Creates a `.bak` backup of any target icon before replacement.
    5.  **Replace**: Overwrites the target icon with the processed Pop!_OS logo.

## Usage

### Prerequisites
- Python 3
- `sudo` privileges (for replacing system-wide icons in `/usr/share/icons`)

### Execution
To replace icons for the current user (no `sudo` needed for `~/.local`):
```bash
python3 replace_app_grid_icon.py
```

To replace system-wide icons (requires `sudo`):
```bash
sudo python3 replace_app_grid_icon.py
```

### Options
- `--dry-run`: Run without checking or modifying files (simulates the process).
- `--logo [PATH]`: Use a specific local SVG file instead of downloading.

## Verification
After running the script, reload the GNOME Shell:
1.  Press `Alt` + `F2`.
2.  Type `r`.
3.  Press `Enter`.

Alternatively, log out and log back in. The app grid icon should now display the custom Pop!_OS logo.
