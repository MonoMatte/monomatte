import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    oppgave_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    UNIQUE(user_id, oppgave_id)
)
""")

conn.commit()
conn.close()

print("Progress-tabellen ble laget!")
