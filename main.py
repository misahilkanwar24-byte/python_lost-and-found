"""
main.py - text menu of the Smart Campus Lost and Found System.

Run:  python main.py
Data is stored in the file campus_lf.db (created automatically, next to this file).
"""
import sqlite3
from datetime import date, datetime

import lost_found as lf
from demo import load_sample_data

MENU = """
==============================================
   SMART CAMPUS LOST AND FOUND SYSTEM
==============================================
 1. Register a student
 2. Report a LOST item
 3. Report a FOUND item
 4. Find matches for a lost report
 5. Verify ownership and return an item
 6. Show all lost items
 7. Show all found items
 8. Show saved matches
 9. Summary report
10. Export lost items to CSV
11. Load the sample data of the report
 0. Exit
"""


def ask(prompt, required=True):
    while True:
        value = input(prompt).strip()
        if value or not required:
            return value
        print("  This field cannot be empty.")


def ask_date(prompt):
    """Ask for a date in YYYY-MM-DD form (press Enter for today)."""
    while True:
        value = input(prompt + " [YYYY-MM-DD, Enter = today]: ").strip()
        if not value:
            return date.today().isoformat()
        try:
            datetime.fromisoformat(value)
            return value
        except ValueError:
            print("  Please type the date like 2026-10-25.")


def show(rows, headers):
    if not rows:
        print("  (no records)")
        return
    widths = [max(len(h), *(len(str(r[i])) for r in rows))
              for i, h in enumerate(headers)]
    line = "  ".join(h.ljust(w) for h, w in zip(headers, widths))
    print(line)
    print("-" * len(line))
    for r in rows:
        print("  ".join(str(v if v is not None else "").ljust(w)
                        for v, w in zip(r, widths)))


def main():
    con = lf.connect()
    while True:
        print(MENU)
        choice = input("Choose an option: ").strip()
        try:
            if choice == "1":
                lf.add_student(con, ask("Student ID : "), ask("Name       : "),
                               ask("Phone      : "), ask("E-mail     : ", False))
                print("Student saved.")

            elif choice == "2":
                lid = lf.report_lost(
                    con, ask("Your student ID : "), ask("Item name       : "),
                    ask("Category (Wallet, Bottle, Keys...): "),
                    ask("Colour (optional) : ", False),
                    ask("Where was it lost : "), ask_date("Date lost"))
                print(f"Lost report saved with ID {lid}.")
                res = lf.find_matches(con, lid)
                if res:
                    print("Possible matches found:")
                    for fid, name, score in res:
                        print(f"  Found ID {fid}: {name}  (score {score}/100)")
                else:
                    print("No match yet. The report stays Open and is checked "
                          "again when a new found item is reported.")

            elif choice == "3":
                fid = lf.report_found(
                    con, ask("Finder student ID : "), ask("Item name        : "),
                    ask("Category           : "),
                    ask("Colour (optional)  : ", False),
                    ask("Where was it found : "), ask_date("Date found"),
                    ask("Secret mark (e.g. sticker inside; used for proof): ",
                        False))
                print(f"Found report saved with ID {fid}.")

            elif choice == "4":
                res = lf.find_matches(con, int(ask("Lost ID: ")))
                if res:
                    for fid, name, score in res:
                        print(f"  Found ID {fid}: {name}  (score {score}/100)")
                else:
                    print("No match above the threshold of", lf.THRESHOLD)

            elif choice == "5":
                print(lf.verify_and_return(
                    con, int(ask("Match ID: ")),
                    ask("Owner's description of the secret mark: "),
                    date.today().isoformat()))

            elif choice == "6":
                show(con.execute("SELECT lost_id, student_id, item_name, "
                                 "category, color, location, lost_date, status "
                                 "FROM lost_item").fetchall(),
                     ["ID", "Student", "Item", "Category", "Colour",
                      "Place", "Date", "Status"])

            elif choice == "7":
                show(con.execute("SELECT found_id, finder_id, item_name, "
                                 "category, color, location, found_date, status "
                                 "FROM found_item").fetchall(),
                     ["ID", "Finder", "Item", "Category", "Colour",
                      "Place", "Date", "Status"])

            elif choice == "8":
                show(con.execute("SELECT match_id, lost_id, found_id, score, "
                                 "status, handover_date FROM match_record"
                                 ).fetchall(),
                     ["Match", "Lost", "Found", "Score", "Status", "Handover"])

            elif choice == "9":
                s = lf.summary(con)
                print(f"Lost reports : {s['lost']}\nFound reports: {s['found']}\n"
                      f"Recovered    : {s['recovered']}\n"
                      f"Recovery rate: {s['rate']} %")

            elif choice == "10":
                n = lf.export_csv(con)
                print(f"{n} rows written to lost_items.csv" if n
                      else "Nothing to export yet.")

            elif choice == "11":
                load_sample_data(con)
                print("Sample data loaded (5 students, 3 lost and 3 found reports).")

            elif choice == "0":
                print("Goodbye!")
                break
            else:
                print("Please choose a number from the menu.")

        except sqlite3.IntegrityError as e:
            print("Database error:", e,
                  "\n(Check that the student ID is registered first.)")
        except ValueError:
            print("Please type a number where a number is needed.")
    con.close()


if __name__ == "__main__":
    main()
