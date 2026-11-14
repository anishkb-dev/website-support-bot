"""Render the gig images from a REAL answer of the running bot (pip install pillow).
Usage: python assets/make_gig_image.py [api_url]   (server must be running with samples ingested)"""
import json, sys, textwrap, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

API = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8765"


def ask(q):
    req = urllib.request.Request(f"{API}/ask", json.dumps({"question": q}).encode(), {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=300))


CHAT = [(q, ask(q)) for q in ("Can I return an opened bag?", "Do you sell gift cards?")]

H = "/System/Library/Fonts/HelveticaNeue.ttc"
f = lambda s, b=False: ImageFont.truetype(H, s, index=1 if b else 0)
BG, GREEN, WHITE, BRAND = (15, 42, 36), (110, 231, 183), (255, 255, 255), (31, 94, 75)


def render(W, Hh, out):
    im = Image.new("RGB", (W, Hh), BG)
    d = ImageDraw.Draw(im)
    s = W / 1280 if W >= 1280 else 0.86  # 4:3 version is narrower: shrink the type
    y0 = (Hh - 769) // 2 + 120
    d.text((60, y0), "AI support chat", font=f(int(62 * s), True), fill=WHITE)
    d.text((60, y0 + 72 * s), "for your website", font=f(int(62 * s), True), fill=GREEN)
    d.text((60, y0 + 148 * s), "answers from your own content", font=f(int(28 * s)), fill=(200, 220, 212))
    for i, t in enumerate(["Answers from your FAQ & docs", "Shows the source",
                           "Says \"not sure\" instead of guessing", "One line to add to any site"]):
        yy = y0 + 220 * s + i * 46 * s
        d.line([(62, yy + 15), (70, yy + 23), (84, yy + 7)], fill=GREEN, width=4)
        d.text((98, yy), t, font=f(int(26 * s)), fill=WHITE)
    tag = '<script src=".../widget.js">'
    ty = y0 + 420 * s
    d.rounded_rectangle((60, ty, 60 + d.textlength(tag, font=f(17)) + 28, ty + 36), 8, fill=(30, 70, 60))
    d.text((74, ty + 8), tag, font=f(17), fill=GREEN)

    # widget mock built from the real API response
    PW = 400 if W >= 1280 else 360
    X, Y, PH = W - PW - 60, (Hh - 680) // 2, 600
    d.rounded_rectangle((X, Y, X + PW, Y + PH), 16, fill=(246, 247, 246))
    d.rounded_rectangle((X, Y, X + PW, Y + 54), 16, fill=BRAND)
    d.rectangle((X, Y + 38, X + PW, Y + 54), fill=BRAND)
    d.text((X + 18, Y + 16), "Northwind Coffee Support", font=f(19, True), fill=WHITE)
    y = Y + 76
    for q, res in CHAT:
        qw = d.textlength(q, font=f(17)) + 28
        d.rounded_rectangle((X + PW - 18 - qw, y, X + PW - 18, y + 40), 14, fill=BRAND)
        d.text((X + PW - 18 - qw + 14, y + 10), q, font=f(17), fill=WHITE)
        lines = textwrap.wrap(res["answer"], 36 if PW == 400 else 32)
        src = ", ".join(f"{x['source']} › {x['location']}" for x in res["sources"])
        by = y + 56
        bh = 24 + len(lines) * 25 + (34 if src else 0)
        d.rounded_rectangle((X + 18, by, X + PW - 40, by + bh), 14, fill=WHITE, outline=(226, 229, 227))
        for i, l in enumerate(lines):
            d.text((X + 32, by + 12 + i * 25), l, font=f(17), fill=(35, 35, 35))
        if src:
            d.text((X + 32, by + 18 + len(lines) * 25), f"Source: {src}", font=f(14), fill=(107, 112, 109))
        y = by + bh + 18
    # input bar
    d.line([(X, Y + PH - 60), (X + PW, Y + PH - 60)], fill=(226, 229, 227))
    d.rounded_rectangle((X + 14, Y + PH - 46, X + PW - 90, Y + PH - 12), 8, fill=WHITE, outline=(207, 212, 209))
    d.text((X + 26, Y + PH - 37), "Type your question...", font=f(15), fill=(150, 150, 150))
    d.rounded_rectangle((X + PW - 80, Y + PH - 46, X + PW - 14, Y + PH - 12), 8, fill=BRAND)
    d.text((X + PW - 66, Y + PH - 37), "Send", font=f(15, True), fill=WHITE)
    # chat bubble button
    cx, cy = X + PW - 28, Y + PH + 44
    d.ellipse((cx - 28, cy - 28, cx + 28, cy + 28), fill=BRAND)
    d.rounded_rectangle((cx - 13, cy - 10, cx + 13, cy + 8), 5, fill=WHITE)
    d.polygon([(cx - 6, cy + 7), (cx - 10, cy + 15), (cx + 1, cy + 7)], fill=WHITE)
    d.text((X, Y + PH + 30), "Real answers from the demo (local model)", font=f(14), fill=(160, 190, 178))
    im.save(out)


here = Path(__file__).parent
render(1280, 769, here / "gig-image.png")
render(1024, 768, here / "gig-4x3.png")
print(CHAT)
