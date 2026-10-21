#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ung dung thi trac nghiem tieng Anh chuyen nganh tai chinh - ngan hang."""
import json
import os
import sqlite3
import time
from datetime import datetime
from flask import (Flask, render_template, request, jsonify, redirect,
                   url_for, session, abort)

BASE = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_PATH = os.path.join(BASE, "questions.json")
DB_PATH = os.environ.get("DB_PATH", os.path.join(BASE, "results.db"))
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "admin123")
TEST_TIME_SEC = 90 * 60  # 90 phut

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-me-in-prod")

# ---------- du lieu de ----------
with open(QUESTIONS_PATH, encoding="utf-8") as f:
    TESTS = json.load(f)  # {"0": [q,...], ...}

TEST_TITLES = {
    "0": "De 1 - Tu vong co ban (A)",
    "1": "De 2 - Tu vong co ban (B)",
    "2": "De 3 - Tu vong trung cap (A)",
    "3": "De 4 - Tu vong trung cap (B)",
    "4": "De 5 - Tu vong nang cao (A)",
    "5": "De 6 - Tu vong nang cao (B)",
    "6": "De 7 - Tong hop (A)",
    "7": "De 8 - Tong hop (B)",
    "8": "De 9 - Tong hop (C)",
    "9": "De 10 - Tong hop (D)",
}


def get_qmap(test_id):
    return {q["id"]: q for q in TESTS[str(test_id)]}


# ---------- DB ----------
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT NOT NULL,
            test_id TEXT NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            started_at TEXT NOT NULL,
            submitted_at TEXT NOT NULL,
            duration_sec INTEGER NOT NULL,
            details TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


init_db()


# ---------- routes ----------
@app.route("/")
def index():
    tests = []
    for tid, qs in TESTS.items():
        tests.append({
            "id": tid,
            "title": TEST_TITLES.get(tid, f"De {int(tid)+1}"),
            "count": len(qs),
            "time_min": 90,
        })
    return render_template("index.html", tests=tests)


@app.route("/test/<test_id>")
def take_test(test_id):
    if str(test_id) not in TESTS:
        abort(404)
    return render_template("test.html", test_id=test_id,
                           title=TEST_TITLES.get(str(test_id), f"De {int(test_id)+1}"),
                           count=len(TESTS[str(test_id)]),
                           time_sec=TEST_TIME_SEC)


@app.route("/api/questions/<test_id>")
def api_questions(test_id):
    if str(test_id) not in TESTS:
        abort(404)
    # khong gui dap an dung ve client
    out = []
    for q in TESTS[str(test_id)]:
        out.append({
            "id": q["id"],
            "term": q["term"],
            "type": q["type"],
            "stem": q["stem"],
            "options": q["options"],
        })
    return jsonify({"test_id": test_id, "questions": out, "time_sec": TEST_TIME_SEC})


@app.route("/api/submit", methods=["POST"])
def api_submit():
    data = request.get_json(force=True)
    test_id = str(data.get("test_id"))
    user_name = (data.get("user_name") or "").strip() or "An danh"
    answers = data.get("answers") or {}
    started_at = data.get("started_at")
    if test_id not in TESTS:
        abort(400)

    qmap = get_qmap(test_id)
    total = len(qmap)
    score = 0
    details = []
    for qid, q in qmap.items():
        user_ans = answers.get(qid)
        correct = q["correct_letter"]
        is_correct = (user_ans == correct)
        if is_correct:
            score += 1
        details.append({
            "qid": qid,
            "term": q["term"],
            "type": q["type"],
            "stem": q["stem"],
            "options": q["options"],
            "user_answer": user_ans,
            "correct_answer": correct,
            "is_correct": is_correct,
            "explanation": q["explanation"],
        })

    now = datetime.now().isoformat(timespec="seconds")
    started = started_at or now
    try:
        t0 = datetime.fromisoformat(started)
        duration = int((datetime.now() - t0).total_seconds())
    except Exception:
        duration = 0
    duration = max(0, min(duration, TEST_TIME_SEC + 60))

    conn = db()
    cur = conn.execute(
        "INSERT INTO attempts (user_name, test_id, score, total, started_at, submitted_at, duration_sec, details) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (user_name, test_id, score, total, started, now, duration, json.dumps(details, ensure_ascii=False)),
    )
    conn.commit()
    attempt_id = cur.lastrowid
    conn.close()

    return jsonify({"attempt_id": attempt_id, "score": score, "total": total})


@app.route("/result/<int:attempt_id>")
def result(attempt_id):
    conn = db()
    row = conn.execute("SELECT * FROM attempts WHERE id=?", (attempt_id,)).fetchone()
    conn.close()
    if not row:
        abort(404)
    details = json.loads(row["details"])
    return render_template("result.html", attempt=row, details=details,
                           titles=TEST_TITLES,
                           title=TEST_TITLES.get(row["test_id"], f"De {int(row['test_id'])+1}"))


@app.route("/admin")
def admin():
    token = request.args.get("token", "")
    if token != ADMIN_TOKEN:
        return render_template("admin_login.html"), 401
    conn = db()
    rows = conn.execute(
        "SELECT id, user_name, test_id, score, total, started_at, submitted_at, duration_sec "
        "FROM attempts ORDER BY submitted_at DESC"
    ).fetchall()
    conn.close()
    attempts = [dict(r) for r in rows]
    # thong ke
    stats = {}
    for a in attempts:
        stats.setdefault(a["test_id"], {"n": 0, "sum": 0, "max": 0})
        stats[a["test_id"]]["n"] += 1
        stats[a["test_id"]]["sum"] += a["score"]
        stats[a["test_id"]]["max"] = max(stats[a["test_id"]]["max"], a["score"])
    for tid, s in stats.items():
        s["avg"] = round(s["sum"] / s["n"], 1) if s["n"] else 0
    return render_template("admin.html", attempts=attempts, stats=stats,
                           titles=TEST_TITLES, token=token)


@app.route("/api/report")
def api_report():
    token = request.args.get("token", "")
    if token != ADMIN_TOKEN:
        abort(401)
    conn = db()
    rows = conn.execute(
        "SELECT id, user_name, test_id, score, total, started_at, submitted_at, duration_sec "
        "FROM attempts ORDER BY submitted_at DESC"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
