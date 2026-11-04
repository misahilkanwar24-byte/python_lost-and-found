"""
Smart Campus Lost and Found System - core module
Subject : Python Programming
Student : SAHIL KANWAR (UID 25BCD10303), BCA (Data Science), Chandigarh University

This file holds the database setup and all the functions of the project:
    add_student, report_lost, report_found, match_score, find_matches,
    verify_and_return, summary and export_csv.
Only the Python standard library is used (sqlite3, difflib, csv, datetime).
"""
import csv
import sqlite3
from datetime import datetime
from difflib import SequenceMatcher

DB_NAME = "campus_lf.db"
THRESHOLD = 60          # minimum match score (out of 100) to suggest a match

SCHEMA = """
CREATE TABLE IF NOT EXISTS student (
    student_id TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    phone      TEXT NOT NULL,
    email      TEXT
);
CREATE TABLE IF NOT EXISTS lost_item (
    lost_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    item_name  TEXT NOT NULL,
    category   TEXT NOT NULL,
    color      TEXT,
    location   TEXT NOT NULL,
    lost_date  TEXT NOT NULL,
    status     TEXT DEFAULT 'Open',
    FOREIGN KEY (student_id) REFERENCES student(student_id)
);
CREATE TABLE IF NOT EXISTS found_item (
    found_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    finder_id   TEXT NOT NULL,
    item_name   TEXT NOT NULL,
    category    TEXT NOT NULL,
    color       TEXT,
    location    TEXT NOT NULL,
    found_date  TEXT NOT NULL,
    secret_mark TEXT,
    status      TEXT DEFAULT 'Unclaimed',
    FOREIGN KEY (finder_id) REFERENCES student(student_id)
);
CREATE TABLE IF NOT EXISTS match_record (
    match_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    lost_id       INTEGER NOT NULL,
    found_id      INTEGER NOT NULL,
    score         REAL NOT NULL,
    status        TEXT DEFAULT 'Suggested',
    handover_date TEXT,
    FOREIGN KEY (lost_id)  REFERENCES lost_item(lost_id),
    FOREIGN KEY (found_id) REFERENCES found_item(found_id)
);
"""


def connect(path=DB_NAME):
    """Open (and create, if needed) the database with foreign keys switched on."""
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(SCHEMA)
    return con


# ----------------------------------------------------------------------------
# Matching logic
# ----------------------------------------------------------------------------
def similar(a, b):
    """Text similarity between 0 and 1 (ignores case and spaces at the ends)."""
    return SequenceMatcher(None, str(a).strip().lower(), str(b).strip().lower()).ratio()


def match_score(lost, found):
    """Score a lost report against a found report (0 to 100).

    Category 30 + item name 30 + colour 15 + location 15 + date 10.
    The found item must have been found 0 to 14 days after the loss,
    otherwise the score is 0.
    """
    score = 0.0
    if lost["category"].lower() == found["category"].lower():
        score += 30                                                # category
    score += 30 * similar(lost["item_name"], found["item_name"])   # name
    if lost["color"] and found["color"]:
        score += 15 * similar(lost["color"], found["color"])       # colour
    score += 15 * similar(lost["location"], found["location"])     # place
    gap = (datetime.fromisoformat(found["found_date"])
           - datetime.fromisoformat(lost["lost_date"])).days
    if not 0 <= gap <= 14:                                         # must be found within
        return 0.0                                                 # 14 days after loss
    if gap <= 7:
        score += 10 * (1 - gap / 7)                                # date closeness
    return round(score, 1)


STOP = {"a", "an", "the", "of", "on", "in", "with", "inside", "and"}


def proof_ok(proof, secret):
    """True if at least half of the secret-mark words appear in the proof."""
    words = lambda t: {w for w in str(t).lower().split() if w not in STOP}
    need = words(secret)
    return bool(need) and len(need & words(proof)) / len(need) >= 0.5


# ----------------------------------------------------------------------------
# Reporting
# ----------------------------------------------------------------------------
def add_student(con, sid, name, phone, email=None):
    con.execute("INSERT OR IGNORE INTO student VALUES (?,?,?,?)",
                (sid, name, phone, email))
    con.commit()


def report_lost(con, sid, item, cat, color, loc, date):
    cur = con.execute("INSERT INTO lost_item (student_id,item_name,category,"
                      "color,location,lost_date) VALUES (?,?,?,?,?,?)",
                      (sid, item, cat, color, loc, date))
    con.commit()
    return cur.lastrowid


def report_found(con, fid, item, cat, color, loc, date, secret=""):
    cur = con.execute("INSERT INTO found_item (finder_id,item_name,category,"
                      "color,location,found_date,secret_mark) "
                      "VALUES (?,?,?,?,?,?,?)",
                      (fid, item, cat, color, loc, date, secret))
    con.commit()
    return cur.lastrowid


def find_matches(con, lost_id):
    """Compare one lost report with all unclaimed found items.

    Returns a list of (found_id, item_name, score) with score >= THRESHOLD,
    best first. Every suggestion is saved in match_record (only once).
    """
    lost = con.execute("SELECT * FROM lost_item WHERE lost_id=?",
                       (lost_id,)).fetchone()
    if lost is None:
        return []
    founds = con.execute("SELECT * FROM found_item "
                         "WHERE status='Unclaimed'").fetchall()
    ranked = sorted(((match_score(lost, f), f) for f in founds),
                    key=lambda x: x[0], reverse=True)
    result = []
    for score, f in ranked:
        if score >= THRESHOLD:
            already = con.execute("SELECT 1 FROM match_record "
                                  "WHERE lost_id=? AND found_id=?",
                                  (lost_id, f["found_id"])).fetchone()
            if not already:
                con.execute("INSERT INTO match_record (lost_id,found_id,score) "
                            "VALUES (?,?,?)", (lost_id, f["found_id"], score))
            result.append((f["found_id"], f["item_name"], score))
    con.commit()
    return result


def verify_and_return(con, match_id, proof, today):
    """Hand over the item only if the owner's proof matches the secret mark."""
    m = con.execute("SELECT m.*, f.secret_mark FROM match_record m "
                    "JOIN found_item f ON m.found_id=f.found_id "
                    "WHERE match_id=?", (match_id,)).fetchone()
    if m is None:
        return "Match not found"
    if m["status"] == "Returned":
        return "Item was already returned"
    if not proof_ok(proof, m["secret_mark"]):
        return "Verification failed - item not handed over"
    con.execute("UPDATE match_record SET status='Returned', handover_date=? "
                "WHERE match_id=?", (today, match_id))
    con.execute("UPDATE lost_item SET status='Recovered' WHERE lost_id=?",
                (m["lost_id"],))
    con.execute("UPDATE found_item SET status='Returned' WHERE found_id=?",
                (m["found_id"],))
    con.commit()
    return "Verified - item returned to owner"


# ----------------------------------------------------------------------------
# Reports
# ----------------------------------------------------------------------------
def summary(con):
    q = lambda sql: con.execute(sql).fetchone()[0]
    lost, rec = (q("SELECT COUNT(*) FROM lost_item"),
                 q("SELECT COUNT(*) FROM lost_item WHERE status='Recovered'"))
    return {"lost": lost, "found": q("SELECT COUNT(*) FROM found_item"),
            "recovered": rec,
            "rate": round(100 * rec / lost, 1) if lost else 0.0}


def export_csv(con, filename="lost_items.csv"):
    rows = con.execute("SELECT * FROM lost_item").fetchall()
    if not rows:
        return 0
    with open(filename, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(rows[0].keys())
        w.writerows([tuple(r) for r in rows])
    return len(rows)
