# Job Scraper & Tracker

A personal job search tool that scrapes listings from LinkedIn and Indeed, scores them by relevance, and lets you track your applications through a browser interface.
Built by an economist with zero programming experience. It's designed to be as simple and intuitive as possible, because life is already hard enough for job seekers.

No Python, no dependencies, no complicated setup. If you can read, you can get this running in under 15 minutes (excluding scraping time).

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

You only need two things installed: **Docker Desktop** and *nothing else*. No Python required.

**1. Install Docker Desktop**

Download from [docker.com](https://www.docker.com/products/docker-desktop/) and install it. Once installed, open it and wait until it shows **"Engine running"** in the bottom left. You can leave it running in the background — you won't need to click anything inside it.

**2. Download this project**

Go to the top of this GitHub page, click the green **Code** button, and select **Download ZIP**. Once downloaded, find the ZIP file (probably in your Downloads folder), right-click it, and select **Extract All**. Put the extracted folder somewhere easy to find, like your Desktop.

**3. Open a command window inside the folder**

Open the extracted folder. Click the address bar at the top of the window so it highlights, type `cmd`, and press Enter. A black window will appear — this is where you'll type all the commands below.

**4. Create your config file**

In the black window, run:

```
copy config.example.yaml config.yaml
```

Then open `config.yaml` in Notepad (right-click the file → Open with → Notepad) and fill in your own search terms and cities. This is the only file you'll ever need to edit. Save and close when done.

**5. Build the app**

In the black window, run:

```
docker compose build
```

This sets everything up inside Docker. It takes a few minutes the first time — you'll see a lot of output. Wait until it finishes and you see your prompt again.

**6. Run the scraper**

```
docker compose run --rm scraper
```

This fetches job listings and saves them to a local database. You should see job counts printed for each city. This means it worked.

**7. Open the web app**

```
docker compose up app
```

Then open your browser and go to **http://localhost:5000**

You should see your job tracker with the scraped jobs.

To stop the app, go back to the black window and press **Ctrl+C**.

---

## Daily workflow

1. Open Docker Desktop and make sure it's running
2. Open the black window in your project folder (same as Setup step 3)
3. Run the scraper: `docker compose run --rm scraper`
4. Start the web app: `docker compose up app`
5. Go to **http://localhost:5000** in your browser
6. Review new jobs, set a status on ones you're interested in
7. Tick the referral checkbox if you applied via a referral
8. Hit **Clear unreviewed** to dismiss the rest
9. Press **Ctrl+C** in the black window to stop the app when done

Applied and interviewing jobs stay pinned at the top across sessions.

---

## Configuration

Everything is controlled from `config.yaml`. Open it in any text editor to make changes.

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

Statuses are set via the dropdown in the UI. The app automatically moves stale jobs through the lifecycle each time you run the scraper.

---

## Tech stack

- **Python** — scraping, filtering, scoring, database writes
- **jobspy** — LinkedIn and Indeed scraping
- **SQLite** — local database, no server needed
- **Flask** — lightweight web framework for the UI
- **Docker** — runs everything without needing Python installed
- **Chart.js** — stats page visualisations

---

## License

MIT

## Contact

Chi Nguyen, chi.nguyen@economics.gu.se 
