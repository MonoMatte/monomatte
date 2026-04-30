import sqlite3

conn = sqlite3.connect("database.db")
conn.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'student'
)
""")
conn.commit()
conn.close()

print("Brukertabell laget!")

def create_tables():
    db = sqlite3.connect("database.db")
    cursor = db.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            oppgave_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            UNIQUE(user_id, oppgave_id)
        )
    """)

    db.commit()
    db.close()

