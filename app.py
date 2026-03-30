from flask import Flask, render_template, request, redirect, url_for, jsonify
from storage import init_db, get_all_jobs, get_stats, update_job, delete_unreviewed, get_stats_detail

app = Flask(__name__)

STATUS_ORDER = ["new", "applied", "interviewing", "offer", "rejected"]

def next_status(current):
    if current in ("rejected", "rejected_after_interview"):
        return "new"
    idx = STATUS_ORDER.index(current) if current in STATUS_ORDER else 0
    return STATUS_ORDER[(idx + 1) % len(STATUS_ORDER)]

@app.route("/")
def index():
    status_filter = request.args.get("status")
    jobs = get_all_jobs(status_filter)
    stats = get_stats()
    return render_template("index.html", jobs=jobs, stats=stats, status_filter=status_filter)

@app.route("/update_status/<int:job_id>", methods=["POST"])
def update_status(job_id):
    new_status = request.form.get("force_status") or next_status(request.form.get("current_status"))
    from datetime import date
    applied_date = None
    clear_applied_date = False
    if new_status == "applied":
        applied_date = date.today().isoformat()
    elif new_status == "new":
        clear_applied_date = True
    update_job(job_id, status=new_status, applied_date=applied_date, clear_applied_date=clear_applied_date)
    return {"status": new_status, "applied_date": applied_date or ""}

@app.route("/hide/<int:job_id>", methods=["POST"])
def hide_job(job_id):
    update_job(job_id, status="hidden")
    from storage import get_connection
    with get_connection() as conn:
        conn.execute("UPDATE jobs SET hidden = 1 WHERE id = ?", (job_id,))
    return redirect(request.referrer or url_for("index"))

@app.route("/clear_unreviewed", methods=["POST"])
def clear_unreviewed():
    delete_unreviewed()
    return redirect(url_for("index"))

@app.route("/update_referral/<int:job_id>", methods=["POST"])
def update_referral(job_id):
    referral = 1 if request.form.get("referral") else 0
    update_job(job_id, referral=referral)
    return {"referral": referral}

@app.route("/stats")
def stats_page():
    data = get_stats_detail()
    return render_template("stats.html", data=data)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)