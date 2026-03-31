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
    conn.row_factory = sqlite3.Row  # access columns by name e.g. row["title"]
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
                pass  # duplicate URL — skip silently
        print(f"  {new_count} new jobs saved to database")


# =============================================================================
# WEB APP — read and update jobs
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
                        WHEN 'ignored'                  THEN 5
                        WHEN 'rejected'                 THEN 6
                        WHEN 'rejected_after_interview' THEN 6
                        ELSE 7
                        END,
                   score DESC"""
            ).fetchall()
        return [dict(row) for row in rows]


def update_job(job_id, status=None, notes=None, applied_date=None, referral=None, clear_applied_date=False):
    with get_connection() as conn:
        if status:
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
        result = conn.execute(
            "UPDATE jobs SET hidden = 1 WHERE status = 'new'"
        )
        print(f"  {result.rowcount} unreviewed jobs deleted")

def age_unreviewed():
    today = datetime.date.today().isoformat()
    with get_connection() as conn:
        # new jobs from previous days → ignored
        conn.execute(
            "UPDATE jobs SET status = 'ignored' WHERE status = 'new' AND date_found < ?",
            (today,)
        )
        # ignored jobs older than 3 days → hidden
        conn.execute(
            """UPDATE jobs SET hidden = 1
               WHERE status = 'ignored'
               AND date_found <= date(?, '-3 days')""",
            (today,)
        )
        # applied 7+ days ago with no movement → ghosted
        conn.execute(
            """UPDATE jobs SET status = 'ghosted'
               WHERE status = 'applied'
               AND applied_date <= date(?, '-7 days')""",
            (today,)
        )

def get_stats():
    with get_connection() as conn:
        applied = conn.execute("""
            SELECT COUNT(*) FROM jobs
            WHERE status NOT IN ('new', 'ignored', 'ghosted', 'hidden')
            AND hidden = 0
        """).fetchone()[0]
        in_progress = conn.execute("""
            SELECT COUNT(*) FROM jobs
            WHERE status IN ('applied', 'interviewing')
        """).fetchone()[0]
        rejected = conn.execute("""
            SELECT COUNT(*) FROM jobs
            WHERE status IN ('rejected', 'rejected_after_interview')
        """).fetchone()[0]
        return {
            "applied":     applied,
            "in_progress": in_progress,
            "rejected":    rejected,
        }

def get_stats_detail():
    """Richer stats for the /stats page."""
    with get_connection() as conn:
        # Funnel counts
        applied_total = conn.execute("""
            SELECT COUNT(*) FROM jobs
            WHERE status NOT IN ('new', 'ignored', 'ghosted', 'hidden')
            AND hidden = 0
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

        # Applications per day
        apps_by_day = conn.execute("""
            SELECT applied_date, COUNT(*) as count
            FROM jobs
            WHERE applied_date IS NOT NULL
            GROUP BY applied_date
            ORDER BY applied_date
        """).fetchall()

        # Ghosted
        ghosted = conn.execute("""
            SELECT COUNT(*) FROM jobs WHERE status = 'ghosted'
        """).fetchone()[0]

        # Referral breakdown
        referral_yes = conn.execute("""
            SELECT COUNT(*) FROM jobs
            WHERE status NOT IN ('new', 'ignored', 'ghosted', 'hidden')
            AND hidden = 0 AND referral = 1
        """).fetchone()[0]

        referral_no = conn.execute("""
            SELECT COUNT(*) FROM jobs
            WHERE status NOT IN ('new', 'ignored', 'ghosted', 'hidden')
            AND hidden = 0 AND referral = 0
        """).fetchone()[0]

        return {
            "funnel":      funnel,
            "apps_by_day": [dict(r) for r in apps_by_day],
            "ghosted":     ghosted,
            "referral_yes": referral_yes,
            "referral_no":  referral_no,
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

