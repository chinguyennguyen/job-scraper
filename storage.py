import sqlite3
from pathlib import Path
from config import cfg
import datetime

DB_PATH = Path(__file__).parent / cfg["database"]


# =============================================================================
# CONNECTION
# =============================================================================

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# =============================================================================
# SETUP — run once on first launch
# =============================================================================

def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                title        TEXT,
                company      TEXT,
                location     TEXT,
                city         TEXT,
                score        INTEGER,
                search_term  TEXT,
                job_url      TEXT UNIQUE,
                date_posted  TEXT,
                date_found   TEXT,
                status       TEXT DEFAULT 'new',
                notes        TEXT DEFAULT '',
                applied_date TEXT,
                hidden       INTEGER DEFAULT 0,
                referral     INTEGER DEFAULT 0
            )
        """)
        # Settings table — one row per key, e.g. weekly_goal
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        # Seed default weekly goal if not set
        conn.execute("""
            INSERT OR IGNORE INTO settings (key, value) VALUES ('weekly_goal', '10')
        """)


# =============================================================================
# SETTINGS
# =============================================================================

def get_setting(key):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else None

def set_setting(key, value):
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, str(value))
        )


# =============================================================================
# SCRAPER — save new jobs
# =============================================================================

def save_jobs(df):
    with get_connection() as conn:
        new_count = 0
        for _, row in df.iterrows():
            try:
                conn.execute("""
                    INSERT INTO jobs
                        (title, company, location, city, score, search_term,
                         job_url, date_posted, date_found)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get("title"),
                    row.get("company"),
                    row.get("location"),
                    row.get("city"),
                    row.get("score"),
                    row.get("search_term"),
                    row.get("job_url"),
                    row.get("date_posted"),
                    row.get("date_found"),
                ))
                new_count += 1
            except sqlite3.IntegrityError:
                pass
        print(f"  {new_count} new jobs saved to database")


# =============================================================================
# AGING — run once per day via main.py
# =============================================================================

def age_unreviewed():
    today = datetime.date.today().isoformat()
    with get_connection() as conn:
        # Hide new jobs older than 7 days
        conn.execute(
            """UPDATE jobs SET hidden = 1
               WHERE status = 'new'
               AND date_found <= date(?, '-7 days')""",
            (today,)
        )
        # applied 7+ days ago with no movement → ghosted
        conn.execute(
            """UPDATE jobs SET status = 'ghosted'
               WHERE status = 'applied'
               AND applied_date <= date(?, '-7 days')""",
            (today,)
        )
        # untrack < 7 days old → back to new
        conn.execute(
            """UPDATE jobs SET status = 'new', applied_date = NULL
               WHERE status = 'untrack'
               AND date_found > date(?, '-7 days')""",
            (today,)
        )
        # untrack > 7 days old → hidden
        conn.execute(
            """UPDATE jobs SET hidden = 1, applied_date = NULL
               WHERE status = 'untrack'
               AND date_found <= date(?, '-7 days')""",
            (today,)
        )


# =============================================================================
# WEEKLY PICKS — page 1
# =============================================================================

def get_weekly_picks():
    """Return all visible new jobs from the last 7 days."""
    cutoff = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM jobs
            WHERE hidden = 0
            AND status = 'new'
            AND date_found >= ?
            ORDER BY score DESC
        """, (cutoff,)).fetchall()
        return [dict(r) for r in rows]

def get_weekly_applied_count():
    """Count jobs applied this calendar week (Monday to today)."""
    today = datetime.date.today()
    monday = (today - datetime.timedelta(days=today.weekday())).isoformat()
    with get_connection() as conn:
        count = conn.execute("""
            SELECT COUNT(*) FROM jobs
            WHERE applied_date >= ?
            AND status NOT IN ('new')
        """, (monday,)).fetchone()[0]
        return count


# =============================================================================
# TRACKER — page 2
# =============================================================================

def get_tracker_jobs(status_filter=None):
    """Return all jobs that were ever applied to."""
    with get_connection() as conn:
        if status_filter:
            rows = conn.execute("""
                SELECT * FROM jobs
                WHERE status = ?
                ORDER BY
                    CASE status
                    WHEN 'offer'                    THEN 1
                    WHEN 'interviewing'             THEN 2
                    WHEN 'applied'                  THEN 3
                    WHEN 'ghosted'                  THEN 4
                    WHEN 'rejected'                 THEN 5
                    WHEN 'rejected_after_interview' THEN 5
                    ELSE 6
                    END,
                applied_date DESC
            """, (status_filter,)).fetchall()
        else:
            rows = conn.execute("""
                SELECT * FROM jobs
                WHERE status NOT IN ('new', 'hidden', 'untrack')
                AND status != 'new'
                AND (
                    applied_date IS NOT NULL
                    OR status IN ('ghosted', 'interviewing', 'offer',
                                  'rejected', 'rejected_after_interview')
                )
                ORDER BY
                    CASE status
                    WHEN 'offer'                    THEN 1
                    WHEN 'interviewing'             THEN 2
                    WHEN 'applied'                  THEN 3
                    WHEN 'ghosted'                  THEN 4
                    WHEN 'rejected'                 THEN 5
                    WHEN 'rejected_after_interview' THEN 5
                    ELSE 6
                    END,
                applied_date DESC
            """).fetchall()
        return [dict(r) for r in rows]


# =============================================================================
# WEB APP — shared read/write
# =============================================================================

def get_all_jobs(status_filter=None):
    with get_connection() as conn:
        if status_filter:
            rows = conn.execute(
                "SELECT * FROM jobs WHERE hidden = 0 AND status = ? ORDER BY score DESC",
                (status_filter,)
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT * FROM jobs WHERE hidden = 0
                   ORDER BY
                        CASE status
                        WHEN 'offer'                    THEN 1
                        WHEN 'interviewing'             THEN 2
                        WHEN 'applied'                  THEN 3
                        WHEN 'new'                      THEN 4
                        WHEN 'rejected'                 THEN 5
                        WHEN 'rejected_after_interview' THEN 5
                        ELSE 6
                        END,
                   score DESC"""
            ).fetchall()
        return [dict(row) for row in rows]


def update_job(job_id, status=None, notes=None, applied_date=None, referral=None, clear_applied_date=False):
    with get_connection() as conn:
        if status is not None:
            conn.execute("UPDATE jobs SET status = ? WHERE id = ?", (status, job_id))
        if notes is not None:
            conn.execute("UPDATE jobs SET notes = ? WHERE id = ?", (notes, job_id))
        if applied_date:
            conn.execute("UPDATE jobs SET applied_date = ? WHERE id = ?", (applied_date, job_id))
        if clear_applied_date:
            conn.execute("UPDATE jobs SET applied_date = NULL WHERE id = ?", (job_id,))
        if referral is not None:
            conn.execute("UPDATE jobs SET referral = ? WHERE id = ?", (referral, job_id))


def delete_unreviewed():
    with get_connection() as conn:
        result = conn.execute("UPDATE jobs SET hidden = 1 WHERE status = 'new'")
        print(f"  {result.rowcount} unreviewed jobs hidden")


def get_stats():
    with get_connection() as conn:
        applied = conn.execute("""
            SELECT COUNT(*) FROM jobs
            WHERE status NOT IN ('new', 'ignored', 'hidden')
            AND applied_date IS NOT NULL
        """).fetchone()[0]
        in_progress = conn.execute("""
            SELECT COUNT(*) FROM jobs
            WHERE status IN ('applied', 'interviewing')
        """).fetchone()[0]
        interviewing = conn.execute("""
            SELECT COUNT(*) FROM jobs WHERE status = 'interviewing'
        """).fetchone()[0]
        rejected = conn.execute("""
            SELECT COUNT(*) FROM jobs
            WHERE status IN ('rejected', 'rejected_after_interview')
        """).fetchone()[0]
        ghosted = conn.execute("""
            SELECT COUNT(*) FROM jobs WHERE status = 'ghosted'
        """).fetchone()[0]
        return {
            "applied":      applied,
            "in_progress":  in_progress,
            "interviewing": interviewing,
            "rejected":     rejected,
            "ghosted":      ghosted,
        }


def get_stats_detail():
    with get_connection() as conn:
        applied_total = conn.execute("""
            SELECT COUNT(*) FROM jobs
            WHERE status NOT IN ('new', 'hidden')
            AND applied_date IS NOT NULL
        """).fetchone()[0]

        in_progress = conn.execute("""
            SELECT COUNT(*) FROM jobs WHERE status IN ('applied', 'interviewing')
        """).fetchone()[0]

        interviewing = conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE status = 'interviewing'"
        ).fetchone()[0]

        offer = conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE status = 'offer'"
        ).fetchone()[0]

        rejected = conn.execute("""
            SELECT COUNT(*) FROM jobs
            WHERE status IN ('rejected', 'rejected_after_interview')
        """).fetchone()[0]

        funnel = {
            "applied":      applied_total,
            "in_progress":  in_progress,
            "interviewing": interviewing,
            "offer":        offer,
            "rejected":     rejected,
        }

        apps_by_day = conn.execute("""
            SELECT applied_date, COUNT(*) as count
            FROM jobs
            WHERE applied_date IS NOT NULL
            GROUP BY applied_date
            ORDER BY applied_date
        """).fetchall()

        ghosted = conn.execute("""
            SELECT COUNT(*) FROM jobs WHERE status = 'ghosted'
        """).fetchone()[0]

        # Total applied by referral source
        referral_yes = conn.execute("""
            SELECT COUNT(*) FROM jobs
            WHERE status NOT IN ('new', 'hidden')
            AND applied_date IS NOT NULL AND referral = 1
        """).fetchone()[0]

        referral_no = conn.execute("""
            SELECT COUNT(*) FROM jobs
            WHERE status NOT IN ('new', 'hidden')
            AND applied_date IS NOT NULL AND referral = 0
        """).fetchone()[0]

        # Interviewing (includes offer + rejected_after_interview) by referral source
        # This tells us how many from each source reached interview stage
        interviewing_via_referral = conn.execute("""
            SELECT COUNT(*) FROM jobs
            WHERE status IN ('interviewing', 'offer', 'rejected_after_interview')
            AND referral = 1
        """).fetchone()[0]

        interviewing_direct = conn.execute("""
            SELECT COUNT(*) FROM jobs
            WHERE status IN ('interviewing', 'offer', 'rejected_after_interview')
            AND referral = 0
        """).fetchone()[0]

        # Offer by referral source
        offer_via_referral = conn.execute("""
            SELECT COUNT(*) FROM jobs WHERE status = 'offer' AND referral = 1
        """).fetchone()[0]

        offer_direct = conn.execute("""
            SELECT COUNT(*) FROM jobs WHERE status = 'offer' AND referral = 0
        """).fetchone()[0]

        # Rejected directly (never reached interview) by referral source
        rejected_direct_no_interview = conn.execute("""
            SELECT COUNT(*) FROM jobs
            WHERE status = 'rejected' AND referral = 0
        """).fetchone()[0]

        rejected_direct_via_referral = conn.execute("""
            SELECT COUNT(*) FROM jobs
            WHERE status = 'rejected' AND referral = 1
        """).fetchone()[0]

        # Rejected after interview by referral source
        rejected_after_interview_no_referral = conn.execute("""
            SELECT COUNT(*) FROM jobs
            WHERE status = 'rejected_after_interview' AND referral = 0
        """).fetchone()[0]

        rejected_after_interview_via_referral = conn.execute("""
            SELECT COUNT(*) FROM jobs
            WHERE status = 'rejected_after_interview' AND referral = 1
        """).fetchone()[0]

        # Ghosted by referral source
        ghosted_via_referral = conn.execute("""
            SELECT COUNT(*) FROM jobs WHERE status = 'ghosted' AND referral = 1
        """).fetchone()[0]

        ghosted_direct = conn.execute("""
            SELECT COUNT(*) FROM jobs WHERE status = 'ghosted' AND referral = 0
        """).fetchone()[0]

        return {
            "funnel":                    funnel,
            "apps_by_day":               [dict(r) for r in apps_by_day],
            "ghosted":                   ghosted,
            "referral_yes":              referral_yes,
            "referral_no":               referral_no,
            "interviewing_via_referral": interviewing_via_referral,
            "interviewing_direct":       interviewing_direct,
            "offer_via_referral":        offer_via_referral,
            "offer_direct":              offer_direct,
            "rejected_direct_no_interview":          rejected_direct_no_interview,
            "rejected_direct_via_referral":          rejected_direct_via_referral,
            "rejected_after_interview_no_referral":  rejected_after_interview_no_referral,
            "rejected_after_interview_via_referral": rejected_after_interview_via_referral,
            "ghosted_via_referral":      ghosted_via_referral,
            "ghosted_direct":            ghosted_direct,
        }


def add_job_manually(title, company, city, job_url, date_applied, date_posted=None):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO jobs
                (title, company, location, city, score, job_url,
                 date_posted, date_found, status, applied_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'applied', ?)
        """, (
            title, company, city, city,
            0,
            job_url or None,
            date_posted or None,
            datetime.date.today().isoformat(),
            date_applied or None,
        ))