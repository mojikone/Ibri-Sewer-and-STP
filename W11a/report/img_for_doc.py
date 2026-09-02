"""Build document-sized copies of the figures.

The figure programme writes at 200 dpi and up to 3,730 px wide - right for inspection in GIS
or for an A3 plot, and wrong for a Word file: 100 of them made an 88.3 MB document, which no
one can email and which pushes a repository that already carries a 68 MB GeoPackage toward
GitHub's 100 MB hard limit.

The originals stay in `img/`. This writes `img_doc/` at a width the page can actually use.
A figure placed 16.6 cm wide on A4 at 300 dpi needs about 1,960 px; more is invisible on the
page and costs megabytes. Line art (charts, diagrams) stays PNG because JPEG rings around
text and hairlines; anything carrying a photographic basemap goes to JPEG, where the same
picture costs a fraction as much.

    python img_for_doc.py
"""
import glob
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "img")
DST = os.path.join(HERE, "img_doc")

# 16.6 cm at 300 dpi is 1,960 px. Round up a little for figures that get a full landscape page.
MAX_W = 2200

# Above this share of unique colours the image is carrying a photographic basemap, and PNG is
# the wrong container for it. Below it the image is line art, where JPEG rings around hairlines
# and around the small type these figures depend on.
PHOTO_COLOURS = 8000


def build():
    os.makedirs(DST, exist_ok=True)
    before = after = 0
    rows = []
    for src in sorted(glob.glob(os.path.join(SRC, "*.png"))):
        name = os.path.splitext(os.path.basename(src))[0]
        before += os.path.getsize(src)
        with Image.open(src) as im:
            im = im.convert("RGB")
            if im.width > MAX_W:
                im = im.resize((MAX_W, round(im.height * MAX_W / im.width)),
                               Image.LANCZOS)
            colours = im.getcolors(maxcolors=PHOTO_COLOURS)
            if colours is None:                      # more colours than the cap: photographic
                out = os.path.join(DST, name + ".jpg")
                im.save(out, "JPEG", quality=88, optimize=True, progressive=True)
            else:
                out = os.path.join(DST, name + ".png")
                im.convert("P", palette=Image.ADAPTIVE, colors=256).save(
                    out, "PNG", optimize=True)
        after += os.path.getsize(out)
        rows.append((name, os.path.getsize(src), os.path.getsize(out)))

    rows.sort(key=lambda r: r[1] - r[2], reverse=True)
    print(f"{len(rows)} figures   {before / 1e6:.1f} MB -> {after / 1e6:.1f} MB "
          f"({100 * (1 - after / max(before, 1)):.0f} % smaller)")
    print("biggest savings:")
    for n, b, a in rows[:6]:
        print(f"  {b / 1e6:6.2f} -> {a / 1e6:5.2f} MB   {n}")
    return DST


if __name__ == "__main__":
    build()
