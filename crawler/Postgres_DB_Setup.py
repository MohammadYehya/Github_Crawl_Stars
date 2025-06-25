import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    dbname='crawlerdb',
    user='user',
    password='pass'
)
cur = conn.cursor()

cur.execute('''
CREATE TABLE IF NOT EXISTS repositories (
    id SERIAL PRIMARY KEY,
    repo_id TEXT UNIQUE,
    name TEXT,
    stars INTEGER,
);
''')

conn.commit()
cur.close()
conn.close()
