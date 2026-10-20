"""Render every post in posts.json into 1080x1080 JPEG carousel slides.

Usage:  python render.py            (renders all posts into images/dayNN/)
Edit posts.json, then run this again to rebuild the images.
"""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent
FONTS = ROOT / "fonts"
OUT = ROOT / "images"

SIZE = 1080
MARGIN = 96
BG = (13, 27, 54)          # deep navy
PANEL = (22, 41, 77)
GOLD = (242, 182, 54)
WHITE = (255, 255, 255)
MUTED = (176, 190, 214)
BRAND = "PROACCT INDIA"


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def wrap(draw, text, fnt, width):
    lines = []
    for para in text.split("\n"):
        words, line = para.split(), ""
        for w in words:
            test = f"{line} {w}".strip()
            if draw.textlength(test, font=fnt) <= width:
                line = test
            else:
                if line:
                    lines.append(line)
                line = w
        lines.append(line)
    return lines


def fit(draw, text, name, start, minimum, width, max_height, spacing=1.2):
    """Largest font size that keeps the wrapped text inside the box."""
    size = start
    while size > minimum:
        f = font(name, size)
        lines = wrap(draw, text, f, width)
        if len(lines) * size * spacing <= max_height:
            return f, lines
        size -= 4
    f = font(name, minimum)
    return f, wrap(draw, text, f, width)


def draw_lines(draw, lines, fnt, x, y, fill, spacing=1.2):
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += int(fnt.size * spacing)
    return y


def frame(page, total):
    img = Image.new("RGB", (SIZE, SIZE), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, SIZE, 14], fill=GOLD)
    small = font("Inter-SemiBold.otf", 28)
    d.text((MARGIN, 64), BRAND, font=small, fill=GOLD)
    counter = f"{page}/{total}"
    d.text((SIZE - MARGIN - d.textlength(counter, font=small), 64), counter, font=small, fill=MUTED)
    return img, d


def cover(post, total):
    img, d = frame(1, total)
    width = SIZE - 2 * MARGIN
    f, lines = fit(d, post["cover"]["hook"], "Poppins-Bold.ttf", 92, 56, width, 520, 1.18)
    y = 210
    y = draw_lines(d, lines, f, MARGIN, y, WHITE, 1.18)
    d.rectangle([MARGIN, y + 30, MARGIN + 120, y + 40], fill=GOLD)
    sub = font("Inter-Regular.otf", 40)
    draw_lines(d, wrap(d, post["cover"]["sub"], sub, width), sub, MARGIN, y + 80, MUTED)
    swipe = font("Inter-SemiBold.otf", 34)
    label = "Swipe →"
    d.text((SIZE - MARGIN - d.textlength(label, font=swipe), SIZE - MARGIN - 34), label, font=swipe, fill=GOLD)
    return img


def content(slide, page, total):
    img, d = frame(page, total)
    width = SIZE - 2 * MARGIN
    tf, tlines = fit(d, slide["title"], "Poppins-Bold.ttf", 80, 48, width, 260, 1.15)
    title_h = int(len(tlines) * tf.size * 1.15)
    bf, blines = fit(d, slide["body"], "Inter-Regular.otf", 60, 34, width - 80, SIZE - 2 * 200 - title_h, 1.35)
    box_h = int(len(blines) * bf.size * 1.35) + 80
    block_h = title_h + 40 + box_h
    y = max(170, (SIZE - block_h) // 2 + 10)
    y = draw_lines(d, tlines, tf, MARGIN, y, GOLD, 1.15)
    y += 40
    box_top = y
    d.rounded_rectangle([MARGIN, box_top, SIZE - MARGIN, box_top + box_h], radius=28, fill=PANEL)
    d.rectangle([MARGIN, box_top + 24, MARGIN + 8, box_top + box_h - 24], fill=GOLD)
    draw_lines(d, blines, bf, MARGIN + 44, box_top + 40, WHITE, 1.35)
    return img


def closing(page, total):
    img, d = frame(page, total)
    big = font("Poppins-Bold.ttf", 84)
    y = draw_lines(d, ["Found this", "useful?"], big, MARGIN, 250, WHITE, 1.15)
    mid = font("Inter-SemiBold.otf", 48)
    for i, line in enumerate(["Save it for later", "Share it with a friend", "Follow Proacct India"]):
        cy = y + 70 + i * 92
        d.ellipse([MARGIN, cy + 14, MARGIN + 24, cy + 38], fill=GOLD)
        d.text((MARGIN + 52, cy), line, font=mid, fill=WHITE)
    note = font("Inter-Regular.otf", 28)
    d.text((MARGIN, SIZE - MARGIN - 28), "For education only. Not financial or tax advice.", font=note, fill=MUTED)
    return img


def render_post(post):
    total = len(post["slides"]) + 2
    folder = OUT / f"day{post['id']:02d}"
    folder.mkdir(parents=True, exist_ok=True)
    pages = [cover(post, total)]
    pages += [content(s, i + 2, total) for i, s in enumerate(post["slides"])]
    pages.append(closing(total, total))
    for i, page in enumerate(pages, 1):
        page.save(folder / f"slide{i}.jpg", "JPEG", quality=92)
    return len(pages)


if __name__ == "__main__":
    posts = json.loads((ROOT / "posts.json").read_text(encoding="utf-8"))
    for p in posts:
        n = render_post(p)
        print(f"day{p['id']:02d}: {n} slides  ({p['topic']})")
