# Job Scraper & Tracker

A personal job search tool that scrapes listings from LinkedIn and Indeed, scores them by relevance, and lets you track your applications through a local web interface.

Built with Python, Flask, and SQLite.

![Status](https://img.shields.io/badge/status-active-brightgreen)

---

## What it does

- Scrapes job listings across multiple cities and search terms
- Filters out irrelevant jobs (wrong language, wrong seniority, blocked companies)
- Scores remaining jobs by keyword relevance and company priority
- Tracks application status through a browser UI at `localhost:5000`
- Ages and hides stale jobs automatically on each run

---

## Screenshots

*Main job tracker*
![Job Tracker](screenshots/tracker.png)

*Stats page*
![Stats](screenshots/stats.png)

---

## Setup

### Option A — Docker (recommended)

The easiest way to run the app. No Python installation needed.

**1. Install Docker Desktop**
Download from [docker.com](https://www.docker.com/products/docker-desktop/) and install it.

**2. Download the Sankey chart library**

The stats page uses a chart library that isn't included in this repo. Download it manually:

- Go to: https://cdn.jsdelivr.net/npm/chartjs-chart-sankey/dist/chartjs-chart-sankey.min.js
- Save the file as `chartjs-chart-sankey.min.js` inside the `static/` folder

**3. Create your config file**
```
copy config.example.yaml config.yaml
```
Then open `config.yaml` and fill in your search terms, cities, and preferences.

**4. Build the container**
```
docker compose build
```

**5. Run the scraper**
```
docker compose run --rm scraper
```

**6. Open the web app**
```
docker compose up app
```
Then open your browser at `http://localhost:5000`

---

### Option B — Plain Python

If you prefer to run without Docker.

**1. Install Python 3.11+** from [python.org](https://www.python.org)

**2. Install dependencies**
```
pip install -r requirements.txt
```

**3. Download the Sankey chart library**

Same as step 2 in Option A above.

**4. Create your config file**
```
copy config.example.yaml config.yaml
```

**5. Run the scraper**
```
python main.py
```

**6. Open the web app**
```
python app.py
```
Then open your browser at `http://localhost:5000`

---

## Daily workflow

1. Run the scraper (`docker compose run --rm scraper` or `python main.py`)
2. Open the web app (`docker compose up app` or `python app.py`)
3. Review new jobs in the browser
4. Set status on interesting ones using the dropdown
5. Tick the referral checkbox if you applied via a referral
6. Hit **Clear unreviewed** to dismiss the rest

Applied and interviewing jobs stay pinned at the top across sessions.

---

## Configuration

Everything is controlled from `config.yaml`. No Python knowledge needed.

| Section | What it does |
|---|---|
| `search_terms` | Job titles to search for |
| `cities` | Locations to search, with language filter settings |
| `hours_old` | How recent the listings need to be |
| `scoring.base_keywords` | Job must match at least one to appear at all |
| `scoring.priority_keywords` | Each match adds +1 to the score |
| `scoring.priority_companies` | Matched companies get +2 bonus points |
| `scoring.negative_title_keywords` | Hard exclusion by title |
| `scoring.blocked_companies` | Hard exclusion by company name |
| `scoring.senior_title_keywords` | Score penalty of -3 (not excluded) |
| `language_filters` | Words and phrases that identify German or Swedish postings |

---

## Status lifecycle

| Status | Meaning |
|---|---|
| `new` | Scraped today, not yet reviewed |
| `ignored` | Carried over from a previous day |
| `applied` | You applied — date recorded automatically |
| `interviewing` | Progressed to interview stage |
| `offer` | Received an offer |
| `rejected` | Rejected or withdrawn after applying |
| `rejected_after_interview` | Rejected after reaching interview stage |
| `ghosted` | Applied 7+ days ago with no response (auto-assigned) |

Statuses are set via dropdown in the UI. `age_unreviewed()` runs automatically on each scrape and handles the `ignored`, `ghosted`, and `hidden` transitions.

---

## Project structure

```
job_scraper/
├── templates/
│   ├── index.html          ← main jobs UI
│   └── stats.html          ← stats page
├── static/
│   └── chartjs-chart-sankey.min.js  ← download manually (see setup)
├── config.yaml             ← your personal config (not in repo)
├── config.example.yaml     ← template — copy this to config.yaml
├── config.py               ← loads config.yaml
├── filter.py               ← scoring and filtering logic
├── scraper.py              ← scrapes jobs via jobspy
├── storage.py              ← all database reads and writes
├── main.py                 ← entry point for scraping
├── app.py                  ← Flask web app
├── requirements.txt        ← Python dependencies
├── Dockerfile              ← container definition
├── docker-compose.yml      ← runs scraper and web app as services
└── jobs.db                 ← your database (not in repo, created on first run)
```

---

## Tech stack

- **Python** — scraping, filtering, scoring, database writes
- **jobspy** — LinkedIn and Indeed scraping
- **SQLite** — local database, no server needed
- **Flask** — lightweight web framework for the UI
- **Chart.js + chartjs-chart-sankey** — stats page visualisations

---

## License

MIT
