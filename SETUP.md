# Setup

## Publishing to GitHub Pages

1. Create a repository named **`halyard-cinder`** under your account. Public.
   Leave the description generic and add no topics — see `PUBLISHING.md`.
2. Upload the contents of this folder to the repository root. Not the folder
   itself — `index.html` must sit at the top level.
3. **Settings → Pages → Build and deployment → Source: Deploy from a branch**,
   branch `main`, folder `/ (root)`. Save.
4. Wait for the green check on the Actions tab, then open
   `https://nburhans.github.io/halyard-cinder/`.

If you name the repository something other than `halyard-cinder`, change the link
in `README.md` to match. Nothing else refers to the repository name.

## Why it works without a build step

`index.html` is self-contained: the dataset and every sprite are embedded in it,
gzipped and base64-encoded. No CDN, no stylesheet, no external script, no fonts to
fetch. It renders the same opened from `file://` as it does over HTTPS.

`.nojekyll` is present so GitHub serves the files as-is rather than running them
through Jekyll.

## Browser requirement

The page decompresses its payload with the browser's native `DecompressionStream`
rather than shipping a decompression library. That needs Chrome 80+, Firefox 113+ or
Safari 16.4+. On anything older the page says so plainly instead of rendering blank.

## Rerunning the analysis

`pipeline/` is numbered in dependency order. Stages 05 and 07–10 are Node and need
the damage-calc fork compiled; everything else is Python 3 with no third-party
dependencies. Run `tools/verify_calcs.js` first — if the engine does not reproduce,
nothing downstream of it is worth trusting.
