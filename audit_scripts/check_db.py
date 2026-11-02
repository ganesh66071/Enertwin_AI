import os
import sqlite3
import pandas as pd

print("=== CHECKING APP.DB ===")
if os.path.exists("backend/app.db"):
    conn = sqlite3.connect("backend/app.db")
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cur.fetchall()
    print("backend/app.db tables:", tables)
    for t in tables:
        tname = t[0]
        cur.execute(f"SELECT count(*) FROM {tname}")
        cnt = cur.fetchone()[0]
        print(f"  {tname}: {cnt} rows")
        cur.execute(f"PRAGMA table_info({tname})")
        cols = [c[1] for c in cur.fetchall()]
        print(f"    cols: {cols}")
    conn.close()
else:
    print("backend/app.db not found")

