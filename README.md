# Smart Campus Lost and Found System (Python Programming)

**Student:** SAHIL KANWAR | **UID:** 25BCD10303 | **Course:** BCA (Data Science), Chandigarh University

A console program written in Python with an SQLite database. It stores student, lost-item and
found-item reports, compares a lost report with all unclaimed found items, gives a **match score out of 100**,
and returns an item only after the owner describes the **secret mark**.

Only the Python standard library is used (`sqlite3`, `difflib`, `csv`, `datetime`) – **nothing to install**.

## Files

| File | Purpose |
|---|---|
| `lost_found.py` | Database tables and all functions (add_student, report_lost, report_found, match_score, find_matches, verify_and_return, summary, export_csv) |
| `main.py` | Text menu to use the system |
| `demo.py` | Runs the sample data of the report and prints the output shown in Section 7 |
| `test_lost_found.py` | Unit tests |

## Run in VS Code

1. Install **Python 3.10 or later** and the **Python** extension in VS Code.
2. `File → Open Folder…` and choose this folder (`01_Python_Lost_and_Found`).
3. Open `main.py` and press the **Run ▶** button (top right), or open the terminal (`Ctrl + ``) and type:

```bash
python main.py        # menu program
python demo.py        # sample data and output of the report
python -m unittest -v # tests
```

(On some computers the command is `python3` or `py` instead of `python`.)
You can also press **F5** and pick *Run menu program* or *Run sample data demo*.

## Quick try-out in the menu

1. Option **11** loads the sample data (5 students, 3 lost and 3 found reports).
2. Option **4** → Lost ID `1` shows the match *Wallet – score 82.3*.
3. Option **8** shows the saved match IDs, option **5** → Match ID `1` and the words
   *lion sticker inside the wallet* hands the item over.
4. Option **9** shows the summary report; option **10** exports `lost_items.csv`.

## How the score is calculated

Category 30 + item name 30 + colour 15 + place 15 + date 10 = 100 marks.
Items with a score of **60 or more** are suggested. A found item must be reported 0–14 days after the loss.

The database file (`campus_lf.db` / `campus_lf_demo.db`) is created automatically. Delete it to start fresh.
