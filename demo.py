"""
demo.py - runs the sample data of the project report (Section 7: Output and Testing).

Run:  python demo.py
It creates a fresh database file (campus_lf_demo.db), registers 5 students,
enters 3 lost and 3 found reports, finds the matches, verifies ownership,
prints the summary and exports the lost items to lost_items.csv.
"""
import os
import sqlite3

import lost_found as lf

DEMO_DB = "campus_lf_demo.db"


def load_sample_data(con):
    """Insert the sample students and reports. Returns (lost_ids, found_ids)."""
    students = [
        ("S101", "Rahul Sharma", "9876501234", "rahul@campus.edu"),
        ("S102", "Simran Kaur", "9876505678", "simran@campus.edu"),
        ("S103", "Aman Verma", "9876509012", "aman@campus.edu"),
        ("S104", "Neha Singh", "9876503456", "neha@campus.edu"),
        ("S105", "Karan Mehta", "9876507890", "karan@campus.edu"),
    ]
    for s in students:
        lf.add_student(con, *s)

    lost_ids = [
        lf.report_lost(con, "S101", "Black Wallet", "Wallet", "Black",
                       "Library", "2026-10-12"),
        lf.report_lost(con, "S102", "Blue Water Bottle", "Bottle", "Blue",
                       "Canteen", "2026-10-13"),
        lf.report_lost(con, "S103", "Boat Earphones", "Earphones", "Black",
                       "Hostel", "2026-10-14"),
    ]
    found_ids = [
        lf.report_found(con, "S104", "Wallet", "Wallet", "Black",
                        "Library 2nd floor", "2026-10-13",
                        "sticker of a lion inside"),
        lf.report_found(con, "S105", "Water Bottle", "Bottle", "Blue",
                        "Canteen", "2026-10-14", "name tag KM on the lid"),
        lf.report_found(con, "S104", "Earbuds", "Earphones", "White",
                        "Sports Ground", "2026-10-16", "red charging case"),
    ]
    return lost_ids, found_ids


def main():
    if os.path.exists(DEMO_DB):
        os.remove(DEMO_DB)
    con = lf.connect(DEMO_DB)

    lost_ids, found_ids = load_sample_data(con)
    n = con.execute("SELECT COUNT(*) FROM student").fetchone()[0]
    print(f"Students registered: {n}")

    print("\n--- Lost reports ---")
    print("Lost IDs:", *lost_ids)
    print("\n--- Found reports ---")
    print("Found IDs:", *found_ids)

    print("\n--- Automatic matching ---")
    for lid in lost_ids:
        res = lf.find_matches(con, lid)
        print(f"Lost #{lid}:", res if res else "no match above threshold")

    print("\n--- Match records ---")
    for m in con.execute("SELECT * FROM match_record"):
        print(f"match {m['match_id']}: lost {m['lost_id']} <-> found "
              f"{m['found_id']}  score {m['score']}  {m['status']}")

    print("\n--- Ownership verification ---")
    print("Match 1 wrong proof :",
          lf.verify_and_return(con, 1, "blue pen and a coin", "2026-10-15"))
    print("Match 1 correct proof:",
          lf.verify_and_return(con, 1, "a sticker of a lion inside the wallet",
                               "2026-10-15"))
    print("Match 2 correct proof:",
          lf.verify_and_return(con, 2, "name tag KM on lid", "2026-10-15"))

    print("\n--- Status of all lost items ---")
    for r in con.execute("SELECT s.name, l.item_name, l.status FROM lost_item l "
                         "JOIN student s ON l.student_id = s.student_id"):
        print(f"{r['name']:<14}{r['item_name']:<20}{r['status']}")

    print("\n--- Summary report ---")
    print(lf.summary(con))
    print("\nRows exported to CSV:", lf.export_csv(con))

    print("\n--- Constraint test (foreign key) ---")
    try:
        lf.report_lost(con, "S999", "Keys", "Keys", "Silver", "Block A",
                       "2026-10-20")          # student S999 does not exist
    except sqlite3.IntegrityError as e:
        print("Error:", e)
    con.close()


if __name__ == "__main__":
    main()
