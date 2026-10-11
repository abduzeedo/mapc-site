# MaPC website

Plain HTML, CSS and a little JavaScript. No frameworks, no web fonts, no third-party requests, no cookies.
Published with GitHub Pages at https://mapc.games.

## Edit
- Pages live in `pages/` (HTML for the `<main>` part, with `title:` and `description:` lines on top).
- Settings (download link, Gumroad link, support email, version) are at the top of `build.py`.
- `python3 build.py` regenerates the `.html` files, `sitemap.xml`, `robots.txt`, `favicon.svg` and `CNAME`. Commit the result.
- Preview: open `index.html` in a browser. To see the Wall of Fame, serve the folder: `python3 -m http.server` and open http://localhost:8000.

## Wall of Fame
`supporters.json` is read by the site and by the MaPC app. Rebuild it from a Gumroad sales export with `scripts/supporters-from-gumroad.py` in the app repo, then commit it here.

## Releases
Put `MaPC.dmg`, the engine tarballs and the LGPL source archives on GitHub Releases of this repo. The download button points to `releases/latest/download/MaPC.dmg`, so name the file exactly `MaPC.dmg`.

## Publish (GitHub Pages)
1. Create the repo (public) and push `main`.
2. Settings > Pages > Deploy from branch `main`, folder `/ (root)`. Custom domain `mapc.games`, then tick "Enforce HTTPS".
3. Cloudflare DNS: four A records for `@` (185.199.108.153, .109.153, .110.153, .111.153) and a CNAME `www` to `<owner>.github.io`, all "DNS only".
