from flask import Flask, render_template, request, redirect, url_for, jsonify
from storage import (init_db, get_all_jobs, get_stats, update_job,
                     delete_unreviewed, get_stats_detail,
                     get_weekly_picks, get_weekly_applied_count,
                     get_tracker_jobs, get_setting, set_setting)

app = Flask(__name__)


# =============================================================================
# PAGE 1 — WEEKLY PICKS
# =============================================================================

@app.route("/")
def index():
    jobs        = get_weekly_picks()
    goal        = int(get_setting("weekly_goal") or 10)
    applied     = get_weekly_applied_count()
    recommended = jobs[:goal]
    others      = jobs[goal:]
    return render_template("index.html",
                           recommended=recommended,
                           others=others,
                           goal=goal,
                           applied=applied)

@app.route("/set_goal", methods=["POST"])
def set_goal():
    goal = request.form.get("goal", 10)
    set_setting("weekly_goal", goal)
    return redirect(url_for("index"))

@app.route("/apply/<int:job_id>", methods=["POST"])
def apply_job(job_id):
    from datetime import date
    update_job(job_id, status="applied", applied_date=date.today().isoformat())
    return {"status": "applied", "applied_date": date.today().isoformat()}

@app.route("/unapply/<int:job_id>", methods=["POST"])
def unapply_job(job_id):
    update_job(job_id, status="new", clear_applied_date=True)
    return {"status": "new"}


# =============================================================================
# PAGE 2 — TRACKER
# =============================================================================

@app.route("/tracker")
def tracker():
    status_filter = request.args.get("status")
    jobs  = get_tracker_jobs(status_filter)
    stats = get_stats()
    return render_template("tracker.html", jobs=jobs, stats=stats,
                           status_filter=status_filter)

@app.route("/update_status/<int:job_id>", methods=["POST"])
def update_status(job_id):
    new_status = request.form.get("force_status")
    from datetime import date
    applied_date       = None
    clear_applied_date = False
    if new_status == "applied":
        applied_date = date.today().isoformat()
    update_job(job_id, status=new_status, applied_date=applied_date,
               clear_applied_date=clear_applied_date)
    return {"status": new_status, "applied_date": applied_date or ""}

@app.route("/update_referral/<int:job_id>", methods=["POST"])
def update_referral(job_id):
    referral = int(request.form.get("referral", 0))
    update_job(job_id, referral=referral)
    return {"referral": referral}

@app.route("/hide/<int:job_id>", methods=["POST"])
def hide_job(job_id):
    from storage import get_connection
    with get_connection() as conn:
        conn.execute("UPDATE jobs SET hidden = 1, applied_date = NULL WHERE id = ?", (job_id,))
    return {"status": "hidden"}

@app.route("/add_job", methods=["POST"])
def add_job():
    from storage import add_job_manually
    add_job_manually(
        title        = request.form.get("title"),
        company      = request.form.get("company"),
        city         = request.form.get("city"),
        job_url      = request.form.get("job_url"),
        date_applied = request.form.get("date_applied"),
    )
    return redirect(url_for("tracker"))

@app.route("/untrack/<int:job_id>", methods=["POST"])
def untrack_job(job_id):
    update_job(job_id, status="untrack")
    return {"status": "untrack"}


# =============================================================================
# PAGE 3 — STATS
# =============================================================================

@app.route("/stats")
def stats_page():
    data = get_stats_detail()
    return render_template("stats.html", data=data)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", debug=False)