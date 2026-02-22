#!/usr/bin/env python3
import os
import shutil
import glob
import subprocess
import argparse
import xml.etree.ElementTree as ET
import urllib.request

LOG_URL = "https://raw.githubusercontent.com/pop-os/icon-theme/master/Pop/256x256/places/distributor-logo-pop-os.svg"

def download_logo(url, output_path):
    print(f"Downloading logo from {url}...")
    try:
        urllib.request.urlretrieve(url, output_path)
        print("Download successful.")
        return True
    except Exception as e:
        print(f"Error downloading logo: {e}")
        return False

def process_logo(input_path, output_path):
    """
    Processes the Pop!_OS logo SVG:
    - Makes the outer shape white (#FFFFFF)
    - Makes the inner 'P!' transparent using a mask
    """
    try:
        ET.register_namespace('', "http://www.w3.org/2000/svg")
        tree = ET.parse(input_path)
        root = tree.getroot()
        ns = {'svg': 'http://www.w3.org/2000/svg'}

        # 1. Find the main content group (with matrix transform)
        # Note: We search for the first g that usually contains the content
        # In the 256 file: root -> g (matrix) -> [circle, g (scale)]
        content_g = root.find("svg:g", ns)
        if content_g is None:
            print("Error: Could not find main group in SVG")
            return False

        # 2. Find circle and p_group
        circle = content_g.find("svg:circle", ns)
        p_group = content_g.find("svg:g", ns)

        if circle is None or p_group is None:
            # Fallback or different structure?
            print("Error: Unexpected SVG structure (missing circle or inner group)")
            return False

        # 3. Create Mask in Defs
        defs = root.find("svg:defs", ns)
        if defs is None:
            defs = ET.SubElement(root, "defs")
        
        mask_id = "pop-cutout-mask"
        mask = ET.SubElement(defs, "mask", attrib={
            "id": mask_id,
            "maskContentUnits": "userSpaceOnUse"
        })

        # 4. Add White Rect to Mask (Reveals background)
        # Circle is around 256,256. A large rect covers it.
        # Using a large coverage to be safe.
        ET.SubElement(mask, "rect", attrib={
            "x": "0", "y": "0", "width": "1000", "height": "1000", "fill": "white"
        })

        # 5. Move P_Group to Mask and set to Black (Hides/Cuts out)
        content_g.remove(p_group) # Remove from visible
        mask.append(p_group)      # Add to mask
        p_group.set("fill", "black")
        
        # Ensure p_group opacity is 1 so black is opaque (fully hiding)
        # It had fill="#fff", we changed to black.
        
        # 6. Apply Mask to Circle and set Circle to White
        circle.set("fill", "white")
        circle.set("mask", f"url(#{mask_id})")

        tree.write(output_path)
        print(f"Processed logo saved to {output_path}")
        return True

    except Exception as e:
        print(f"Error processing logo: {e}")
        import traceback
        traceback.print_exc()
        return False

def find_target_icons():
    """Finds all 'view-app-grid-symbolic.svg' files."""
    search_dirs = [
        "/usr/share/icons",
        os.path.expanduser("~/.local/share/icons"),
         os.path.expanduser("~/.icons")
    ]
    
    targets = []
    print("Searching for icons...")
    for d in search_dirs:
        if not os.path.exists(d):
            continue
        # Using find command for speed and recursion
        try:
            cmd = ["find", d, "-name", "view-app-grid-symbolic.svg"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                found = result.stdout.strip().split('\n')
                found = [f for f in found if f] # Filter empty
                targets.extend(found)
        except Exception as e:
            print(f"Error searching in {d}: {e}")
            
    return list(set(targets)) # Unique entries

def replace_icon(target_path, source_icon_path):
    """Backs up and replaces the icon."""
    try:
        backup_path = target_path + ".bak"
        if not os.path.exists(backup_path):
            shutil.copy2(target_path, backup_path)
            print(f"Backed up: {target_path} -> {backup_path}")
        
        # We need to force overwrite even if symlink?
        # If symlink, we might want to replace the link with the file, OR follow it.
        # Usually icon themes have symlinks to reduce duplication.
        # If we replace the symlink with a file, it works for that path.
        if os.path.islink(target_path):
            print(f"Unlinking symlink: {target_path}")
            os.unlink(target_path)

        shutil.copy2(source_icon_path, target_path)
        print(f"Replaced: {target_path}")
    except PermissionError:
        print(f"Permission denied: {target_path}. Try running with sudo.")
    except Exception as e:
        print(f"Error replacing {target_path}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Replace app grid icon with Pop!_OS logo.")
    parser.add_argument("--logo", help="Path to custom logo SVG")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually replace files")
    args = parser.parse_args()

    raw_logo = "pop-os-logo-256.svg"
    final_logo = "processed_pop_logo.svg" 
    
    # 1. Get/Check Logo
    if args.logo:
        raw_logo = args.logo
        if not os.path.exists(raw_logo):
            print(f"Error: Provided logo {raw_logo} not found.")
            return
    elif not os.path.exists(raw_logo):
        # Try to use existing if available, else download
        if not download_logo(LOG_URL, raw_logo):
            return

    # 2. Process the logo
    if not process_logo(raw_logo, final_logo):
        return

    # 3. Find targets
    targets = find_target_icons()
    print(f"Found {len(targets)} matching icons.")

    # 4. Replace
    if args.dry_run:
        print("Dry run enabled. Would replace:")
        for t in targets:
            print(f" - {t}")
    else:
        for t in targets:
            replace_icon(t, final_logo)
            
    print("Done. You may need to log out or reload the shell (Alt+F2 > r) for changes to take effect.")

if __name__ == "__main__":
    main()
