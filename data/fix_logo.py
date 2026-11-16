# Copyright (C) 2026 Chuck Talk <chuck@nordheim.online>
# This file is part of Bender.
#
# Bender is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, version 3.
#
# Bender is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY. See the GNU GPL v3 for details.

import os
from PIL import Image


def get_real_bbox(img):
    """Return the bounding box of non-transparent pixels in an RGBA image."""
    alpha = img.split()[-1]
    return alpha.point(lambda p: 255 if p > 10 else 0).getbbox()


def fix(inf: str, outf: str) -> None:
    """Crop transparent margins and resize logo asset to 96x96."""
    img = Image.open(inf).convert("RGBA")
    bbox = get_real_bbox(img)
    if bbox:
        img = img.crop(bbox)
        img.thumbnail((96, 96), Image.Resampling.LANCZOS)
        img.save(outf)
        print("Saved", outf, "with size", img.size)


if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))
    fix(os.path.join(base, "noln.png"), os.path.join(base, "noln_ui.png"))
    fix(os.path.join(base, "noln_dark.png"), os.path.join(base, "noln_dark_ui.png"))
