# ProxiWall Web

A multi-page project site for **ProxiWall**, a distance-driven semantic zoom
interface for HMD-free virtual museum exploration on a wall display.

## Pages

- `index.html` — project overview
- `concept.html` — interaction modes and project evolution
- `system.html` — tracking, rendering, and interaction pipeline
- `research.html` — interviews, hypotheses, and study design
- `archive.html` — downloadable proposal, interview, midterm, and progress decks

## Local preview

The site is dependency-free. Open `index.html` directly or serve the directory:

```bash
python3 -m http.server 8080
```

Then visit <http://localhost:8080>.

## Deployment

Pushes to `main` automatically deploy the site with GitHub Actions. In the
repository's **Settings → Pages**, set **Source** to **GitHub Actions**.
