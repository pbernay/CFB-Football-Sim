import sqlite3

# Connect to a database (or create one if it doesn't exist)
conn = sqlite3.connect('players.db')
cursor = conn.cursor()

# Create a players table
cursor.execute('''
CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    position TEXT NOT NULL,
    team TEXT,
    touchdowns INTEGER,
    yards_run INTEGER
)
''')

conn.commit()
conn.close()
