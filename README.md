# 🧠 Schulte Table Brain Trainer

Train focus and peripheral vision: find the numbers in order as fast as you can.
Upgraded from an ipywidgets notebook to a full-stack web app.

**Stack:** HTML / CSS / vanilla JS frontend · Flask + SQLite backend (optional)

## Features
- 3×3 to 7×7 grids; **Classic** (1→N), **Reverse** (N→1), **Shuffle** (grid reshuffles after every tap)
- Smooth live timer, +2s penalty per mistake, progress bar, focus dot
- Leaderboard with ranks, personal best detection, progress chart, per-number split chart
- Sound, dark mode, keyboard shortcuts (Enter = start, R = restart), mobile friendly
- **Works with or without the backend**: no server → scores are saved in the browser (localStorage)

## Project structure
```
app.py                  Flask API + SQLite
requirements.txt        Flask, gunicorn
Procfile / render.yaml  backend deploy config
tests/test_api.py       API tests (pytest)
static/
  index.html            page
  style.css             themes + layout
  config.js             API_BASE setting
  api.js                data layer (backend or localStorage)
  script.js             game logic
.github/workflows/      pages.yml (deploy) + test.yml (CI)
```

## Run locally (full stack)
```bash
pip install -r requirements.txt
python app.py            # http://127.0.0.1:5000
```
Frontend only: open `static/index.html` or run `python -m http.server -d static`.

## Deploy option A - GitHub Pages only (simplest)
Scores are stored per browser (local mode).
1. Push this repo to GitHub (branch `main`).
2. Repo **Settings → Pages → Source: GitHub Actions**.
3. The workflow in `.github/workflows/pages.yml` publishes `static/`.
   Your site: `https://<username>.github.io/<repo>/`

## Deploy option B - shared online leaderboard
GitHub Pages cannot run Python, so host the backend elsewhere and keep the frontend on Pages.
1. Deploy the backend on [Render](https://render.com) (New → Web Service → connect repo;
   `render.yaml` is included). Optional env var: `CORS_ORIGIN=https://<username>.github.io`.
2. Edit `static/config.js`:
   ```js
   window.SCHULTE_CONFIG = { API_BASE: "https://your-service.onrender.com" };
   ```
3. Commit and push; Pages redeploys. The badge on the page shows **Online leaderboard**.

Notes: Render's free tier sleeps when idle (the first request can take ~30s; the app falls
back to local mode if it doesn't answer within 4s) and its disk resets on redeploy, so
scores can be lost. For permanent storage use a hosted database.

## API
| Method | Route | Purpose |
|---|---|---|
| GET  | /api/health | backend check |
| POST | /api/scores | save a finished game (validated) |
| GET  | /api/leaderboard?size=5&mode=classic | top 10 |
| GET  | /api/stats?player=Name | best, average, history |

## Tests
```bash
pip install pytest && pytest
```
