import sqlite3

# Create a SQLite database and a table
conn = sqlite3.connect('nba_roster.db')
cursor = conn.cursor()

# Create a table
cursor.execute('''
CREATE TABLE nba_roster (
    NAME TEXT,
    TEAM TEXT,
    SALARY INTEGER
)
''')

# Insert sample data
players = [
    ('Klay Thompson', 'Golden State Warriors', 43219440),
    ('Stephen Curry', 'Golden State Warriors', 48500000),
    ('LeBron James', 'Los Angeles Lakers', 44100000),
    ('Kevin Durant', 'Brooklyn Nets', 42600000),
    ('Giannis Antetokounmpo', 'Milwaukee Bucks', 45400000)
]

cursor.executemany('INSERT INTO nba_roster (NAME, TEAM, SALARY) VALUES (?, ?, ?)', players)

# Commit and close
conn.commit()
conn.close()