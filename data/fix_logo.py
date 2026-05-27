# Copyright (C) 2026 Chuck Talk <cwtalk1@gmail.com>
# This file is part of Bender.
#
# Bender is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, version 3.
#
# Bender is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY. See the GNU AGPL v3 for details.

from PIL import Image

def get_real_bbox(img):
    """get_real_bbox implementation."""
    a = img.split()[-1]
    return a.point(lambda p: p > 10 and 255).getbbox()

def fix(inf, outf):
    """fix implementation."""
    img = Image.open(inf).convert("RGBA")
    bbox = get_real_bbox(img)
    if bbox:
        img = img.crop(bbox)
        img.thumbnail((96, 96), Image.Resampling.LANCZOS)
        img.save(outf)
        print("Saved", outf, "with size", img.size)

fix("/home/freecode/antigrav/Bender/data/noln.png", "/home/freecode/antigrav/Bender/data/noln_ui.png")
fix("/home/freecode/antigrav/Bender/data/noln_dark.png", "/home/freecode/antigrav/Bender/data/noln_dark_ui.png")
