#!/usr/bin/env python3
"""Builds the static pages in this folder from pages/*.html (no dependencies, Python 3 standard library).

  python3 build.py

Each page in pages/ starts with `title:` and `description:` lines (optional `robots:`), a `---` line, then the HTML of <main>.
Placeholders in pages: {{icon:name}}, {{DOWNLOAD_URL}}, {{BUY_URL}}, {{EMAIL}}, {{SITE}}, {{VERSION}}, {{RELEASES}}, {{SOURCE_URL}}.
Edit the settings below, rebuild, and commit the generated .html files.
"""
import html
import pathlib
import re

ROOT = pathlib.Path(__file__).parent
SITE = "https://mapc.games"
EMAIL = "support@mapc.games"
# Steale LLC's mailing address (a registered agent or mailbox address is fine). Shown on the privacy and terms pages when set.
ADDRESS = "Thornhill Dr, Oakland, California 94611, USA"
BUY_URL = "https://abdz.gumroad.com/l/mapcpro"
RELEASES = "https://github.com/abduzeedo/mapc-site/releases"
DOWNLOAD_URL = RELEASES + "/latest/download/MaPC.dmg"
# MacadeKit, the open-source part of MaPC that runs the games (Apache 2.0).
SOURCE_URL = "https://github.com/abduzeedo/mapc-engine"
VERSION = "1.1.14 Beta"

MOCK = """<div class="stage" role="img" aria-label="Illustration of the MaPC library: a sidebar of stores and a grid of game covers with a Play button">
<div class="mock">
<div class="mock-bar"><i></i><i></i><i></i></div>
<div class="mock-body">
<div class="mock-side">
<span class="on">Home</span><span>All Games</span><span>Installed</span>
<b>Stores</b><span>Steam</span><span>Epic Games</span><span>GOG</span>
<b>Activity</b><span>Downloads</span><span>Playtime</span>
</div>
<div class="mock-main">
<div class="mock-title">Ready to Play</div>
<div class="mock-sub">Your installed games, most recent first</div>
<div class="mock-grid">
<div class="cover c1"><span class="play">Play</span></div><div class="cover c2"></div><div class="cover c3"></div><div class="cover c4"></div>
<div class="cover c5"></div><div class="cover c6"></div><div class="cover c7"></div><div class="cover c8"></div>
</div>
</div>
</div>
</div>
<p class="caption">An illustration. Real screenshots are coming.</p>
</div>"""

ICONS = {
    "gamepad": '<path d="M6 8h12a4 4 0 0 1 4 4.2l-.6 4a2.6 2.6 0 0 1-4.5 1.3L15 15.5H9l-1.9 2a2.6 2.6 0 0 1-4.5-1.3l-.6-4A4 4 0 0 1 6 8z"/><path d="M8 11v3M6.5 12.5h3"/><circle cx="15.5" cy="11.5" r=".6"/><circle cx="17.5" cy="13.5" r=".6"/>',
    "bag": '<path d="M5 8h14l-1 12H6L5 8z"/><path d="M9 8a3 3 0 0 1 6 0"/>',
    "cube": '<path d="M12 3l8 4.5v9L12 21l-8-4.5v-9L12 3z"/><path d="M12 12l8-4.5M12 12L4 7.5M12 12v9"/>',
    "sliders": '<path d="M4 7h10M18 7h2M4 17h2M10 17h10"/><circle cx="16" cy="7" r="2"/><circle cx="8" cy="17" r="2"/>',
    "window": '<rect x="3" y="4" width="18" height="16" rx="3"/><path d="M3 9h18"/>',
    "shield": '<path d="M12 3l7 3v5c0 4.5-3 8-7 10-4-2-7-5.5-7-10V6l7-3z"/><path d="M9 12l2 2 4-4"/>',
    "code": '<path d="M8 8l-4 4 4 4M16 8l4 4-4 4M13.5 5l-3 14"/>',
    "backup": '<path d="M7 18a4.5 4.5 0 0 1-.6-8.9A6 6 0 0 1 18 9.5a4 4 0 0 1-.5 8.5H7z"/><path d="M12 15V10M9.5 12.2L12 9.8l2.5 2.4"/>',
    "chart": '<path d="M5 20V10M12 20V4M19 20v-7"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6L7 7M17 17l1.4 1.4M18.4 5.6L17 7M7 17l-1.4 1.4"/>',
    "plusapp": '<rect x="4" y="4" width="16" height="16" rx="4"/><path d="M12 8v8M8 12h8"/>',
    "menubar": '<rect x="3" y="5" width="18" height="14" rx="3"/><path d="M3 9h18M15 7h3"/>',
    "wave": '<path d="M4 12h2M8 8v8M12 5v14M16 8v8M20 12h-2"/>',
    "trophy": '<path d="M8 4h8v5a4 4 0 0 1-8 0V4z"/><path d="M8 6H5a3 3 0 0 0 3 4M16 6h3a3 3 0 0 1-3 4M12 13v4M9 20h6"/>',
    "gauge": '<path d="M4 16a8 8 0 1 1 16 0"/><path d="M12 16l4-5"/>',
    "sparkle": '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3z"/>',
    "command": '<path d="M9 9V6.5A2.5 2.5 0 1 0 6.5 9H9zm0 0h6m-6 0v6m6-6V6.5A2.5 2.5 0 1 1 17.5 9H15zm0 0v6m0 0h2.5a2.5 2.5 0 1 1-2.5 2.5V15zm0 0H9m0 0v2.5A2.5 2.5 0 1 1 6.5 15H9z"/>',
    "download": '<path d="M12 4v11M7.5 11L12 15.5 16.5 11M5 20h14"/>',
}

# The MaPC logo (from the owner's mapc.svg).
LOGO = ('<svg viewBox="0 0 1600 1600" aria-hidden="true"><rect width="1600" height="1600" rx="360" fill="#181818"/>'
        '<path fill="#84273c" d="M969.55,302.78c-71.59,0-130.21,24.49-171.31,71.16-41.11-46.68-99.73-71.16-171.31-71.16-152.31,0-243.25,97.66-243.25,261.23v326.56h196.88v-326.56c0-67.12,31.87-75.72,59.63-75.72,25.61,0,59.64,7.85,59.64,75.72v326.56h196.86v-326.56c0-67.87,34.04-75.72,59.63-75.72,27.77,0,59.64,8.61,59.64,75.72v326.56h196.86v-326.56c0-163.57-90.94-261.23-243.25-261.23Z"/><path fill="#b42f2a" d="M972.46,438.24c-71.59,0-130.21,24.49-171.31,71.16-41.11-46.68-99.73-71.16-171.31-71.16-152.31,0-243.25,97.66-243.25,261.23v326.56h196.88v-326.56c0-67.12,31.87-75.72,59.63-75.72,25.61,0,59.64,7.85,59.64,75.72v326.56h196.86v-326.56c0-67.87,34.04-75.72,59.63-75.72,27.77,0,59.64,8.61,59.64,75.72v326.56h196.86v-326.56c0-163.57-90.94-261.23-243.25-261.23Z"/><path fill="#c25830" d="M972.46,573.7c-71.59,0-130.21,24.49-171.31,71.16-41.11-46.68-99.73-71.16-171.31-71.16-152.31,0-243.25,97.66-243.25,261.23v326.56h196.88v-326.56c0-67.12,31.87-75.72,59.63-75.72,25.61,0,59.64,7.85,59.64,75.72v326.56h196.86v-326.56c0-67.87,34.04-75.72,59.63-75.72,27.77,0,59.64,8.61,59.64,75.72v326.56h196.86v-326.56c0-163.57-90.94-261.23-243.25-261.23Z"/><path fill="#fcb40a" d="M972.46,709.16c-71.59,0-130.21,24.49-171.31,71.16-41.11-46.68-99.73-71.16-171.31-71.16-152.31,0-243.25,97.66-243.25,261.23v326.56h196.88v-326.56c0-67.12,31.87-75.72,59.63-75.72,25.61,0,59.64,7.85,59.64,75.72v326.56h196.86v-326.56c0-67.87,34.04-75.72,59.63-75.72,27.77,0,59.64,8.61,59.64,75.72v326.56h196.86v-326.56c0-163.57-90.94-261.23-243.25-261.23Z"/></svg>')

CSP = ("default-src 'none'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'self'; "
       "base-uri 'none'; form-action 'none'")

NAV = [("features", "Features", "index.html#features", True), ("support", "Support", "index.html#support", True),
       ("wall", "Wall of Fame", "wall.html", True), ("faq", "FAQ", "index.html#faq", True)]


SHOTS = ROOT / "assets" / "screens"
TOUR = [("library", "Your whole library, one place.", "Steam, Epic and GOG side by side, with search and sorting."),
        ("game", "Game pages with their own colors.", "Each game gets a page tinted by its art, with play time, details and settings."),
        ("stats", "Playtime stats.", "Hours per week and store, and your most played. A supporter extra."),
        ("saves", "Settings and save backup.", "Graphics, Retina and more for each game, and one-click save backup to iCloud Drive or any folder. Supporter extras.")]


def image_size(path):
    """Width and height of a PNG or JPEG, read from the file header (no libraries)."""
    import struct
    data = path.read_bytes()
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", data[16:24])
    i = 2
    while i < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            h, w = struct.unpack(">HH", data[i + 5:i + 9])
            return w, h
        i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
    return None


def shot_file(name):
    for ext in ("jpg", "png"):
        f = SHOTS / f"{name}.{ext}"
        if f.exists():
            return f
    return None


def img(f, alt, eager=False):
    w, h = image_size(f) or (1600, 1000)
    load = "" if eager else ' loading="lazy"'
    return f'<img src="assets/screens/{f.name}" width="{w}" height="{h}" alt="{html.escape(alt, quote=True)}"{load}>'


def hero_visual():
    f = shot_file("home")
    if not f:
        return MOCK  # an illustration until real screenshots exist
    return ('<div class="stage shots">' + img(f, "The MaPC home screen: a featured game, and the installed games ready to play", True)
            + '</div>')


def tour():
    figs = []
    for name, title, text in TOUR:
        f = shot_file(name)
        if f:
            figs.append(f'<figure class="shot">{img(f, title)}<figcaption><b>{title}</b> {text}</figcaption></figure>')
    if not figs:
        return ""
    return ('<section id="tour"><p class="eyebrow">A look inside</p><h2>Made for the Mac. <span class="fade">Not a web page in a window.</span></h2>'
            '<div class="tour">' + "".join(figs) + "</div></section>")


def icon(name):
    return ('<svg class="ico" viewBox="0 0 24 24" aria-hidden="true">' + ICONS[name] + "</svg>")


def layout(meta, body, filename):
    title, desc = html.escape(meta["title"], quote=True), html.escape(meta["description"], quote=True)
    url = SITE + "/" + ("" if filename == "index.html" else filename)
    robots = f'\n<meta name="robots" content="{html.escape(meta["robots"], quote=True)}">' if meta.get("robots") else ""
    nav = "".join(f'<li class="hide-sm"><a href="{href}">{label}</a></li>' for _, label, href, _ in NAV)
    ld = ""
    if filename == "index.html":
        ld = ('<script type="application/ld+json">{"@context":"https://schema.org","@type":"SoftwareApplication",'
              '"name":"MaPC","operatingSystem":"macOS 15+","applicationCategory":"GameApplication",'
              f'"description":"{desc}","url":"{SITE}/","publisher":{{"@type":"Organization","name":"Steale LLC"}},'
              '"offers":{"@type":"Offer","price":"0","priceCurrency":"USD"}}</script>')
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{CSP}">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="color-scheme" content="light dark">{robots}
<link rel="canonical" href="{url}">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="icon" href="favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{SITE}/og-image.png">
<link rel="stylesheet" href="styles.css">
{ld}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<div class="wrap nav-shell"><nav class="nav" aria-label="Main">
<a class="brand" href="index.html" aria-label="MaPC home">{LOGO}<span>MaPC</span></a>
<ul>{nav}<li><a class="btn btn-primary btn-sm" href="index.html#download">Download</a></li></ul>
</nav></div>
<main id="main">
{body}
</main>
<footer><div class="wrap">
<div class="foot">
<div class="about"><a class="brand" href="index.html">{LOGO}<span>MaPC</span></a>
<p class="fade">Your PC games, on your Mac.<br>Made by Steale LLC.</p></div>
<div><h4>Product</h4><ul><li><a href="index.html#download">Download</a></li><li><a href="index.html#support">Support MaPC</a></li><li><a href="wall.html">Wall of Fame</a></li><li><a href="changelog.html">What&rsquo;s new</a></li></ul></div>
<div><h4>Help</h4><ul><li><a href="index.html#faq">FAQ</a></li><li><a href="directx12.html">DirectX 12 (advanced)</a></li><li><a href="mailto:{EMAIL}">{EMAIL}</a></li><li><a href="{RELEASES}">All releases</a></li><li><a href="{SOURCE_URL}">Source code (GitHub)</a></li></ul></div>
<div><h4>Legal</h4><ul><li><a href="privacy.html">Privacy</a></li><li><a href="terms.html">Terms &amp; refunds</a></li><li><a href="eula.html">License agreement</a></li><li><a href="opensource.html">Open source</a></li></ul></div>
</div>
<div class="legal">
<p>&copy; <span data-year>2026</span> Steale LLC. All rights reserved.</p>
<p>MaPC isn&rsquo;t affiliated with or endorsed by Valve, Epic Games, GOG, Apple, CodeWeavers, Microsoft or NVIDIA. Steam, Epic Games, GOG, Apple, Mac, macOS, Metal, CrossOver, Microsoft, Windows, DirectX, Direct3D, NVIDIA and DLSS are trademarks of their owners and are used only to identify what MaPC works with or is built from.</p>
</div>
</div></footer>
<script src="site.js" defer></script>
</body>
</html>
"""


def fill(text):
    text = text.replace("{{HERO_VISUAL}}", hero_visual()).replace("{{TOUR}}", tour())
    text = re.sub(r"\{\{icon:(\w+)\}\}", lambda m: icon(m.group(1)), text)
    text = text.replace("{{ADDRESS_LINE}}", f"<p>Mailing address: {html.escape(ADDRESS)}</p>" if ADDRESS else "")
    for key, value in {"DOWNLOAD_URL": DOWNLOAD_URL, "BUY_URL": BUY_URL, "EMAIL": EMAIL, "SITE": SITE,
                       "VERSION": VERSION, "RELEASES": RELEASES, "SOURCE_URL": SOURCE_URL}.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def main():
    for src in sorted((ROOT / "pages").glob("*.html")):
        head, _, body = src.read_text(encoding="utf-8").partition("\n---\n")
        meta = dict(line.split(":", 1) for line in head.strip().splitlines())
        meta = {k.strip(): v.strip() for k, v in meta.items()}
        (ROOT / src.name).write_text(layout(meta, fill(body.strip()), src.name), encoding="utf-8")
        print("built", src.name)

    # The license agreement is plain text.
    eula = html.escape((ROOT / "pages" / "eula.txt").read_text(encoding="utf-8").strip())
    body = f'<div class="wrap"><article class="doc"><h1>License agreement</h1><pre>{eula}</pre></article></div>'
    meta = {"title": "License agreement — MaPC", "description": "The MaPC end user license agreement."}
    (ROOT / "eula.html").write_text(layout(meta, body, "eula.html"), encoding="utf-8")
    print("built eula.html")

    (ROOT / "favicon.svg").write_text(LOGO.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" ', 1), encoding="utf-8")
    pages = ["", "wall.html", "changelog.html", "privacy.html", "terms.html", "opensource.html", "eula.html"]
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{SITE}/{p}</loc></url>\n" for p in pages) + "</urlset>\n", encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")
    (ROOT / "CNAME").write_text("mapc.games\n", encoding="utf-8")
    (ROOT / ".nojekyll").write_text("", encoding="utf-8")
    if not (ROOT / "supporters.json").exists():
        (ROOT / "supporters.json").write_text('{\n  "updated": "",\n  "supporters": []\n}\n', encoding="utf-8")


if __name__ == "__main__":
    main()
