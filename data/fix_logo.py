from PIL import Image

def get_real_bbox(img):
    a = img.split()[-1]
    return a.point(lambda p: p > 10 and 255).getbbox()

def fix(inf, outf):
    img = Image.open(inf).convert("RGBA")
    bbox = get_real_bbox(img)
    if bbox:
        img = img.crop(bbox)
        img.thumbnail((96, 96), Image.Resampling.LANCZOS)
        img.save(outf)
        print("Saved", outf, "with size", img.size)

fix("/home/freecode/antigrav/Bender/data/noln.png", "/home/freecode/antigrav/Bender/data/noln_ui.png")
fix("/home/freecode/antigrav/Bender/data/noln_dark.png", "/home/freecode/antigrav/Bender/data/noln_dark_ui.png")
