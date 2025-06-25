from Github_Client import GitHubClient
import psycopg2
import os
import time

client = GitHubClient(os.getenv("GITHUB_TOKEN"))
conn = psycopg2.connect(
    host=os.getenv('PGHOST'),
    port=os.getenv('PGPORT'),
    dbname=os.getenv('PGDATABASE'),
    user=os.getenv('PGUSER'),
    password=os.getenv('PGPASSWORD')
)
cur = conn.cursor()

query = """
query ($cursor: String, $queryStr: String!) {
  search(query: $queryStr, type: REPOSITORY, first: 100, after: $cursor) {
    pageInfo {
      endCursor
      hasNextPage
    }
    nodes {
      ... on Repository {
        id
        nameWithOwner
        stargazerCount
      }
    }
  }
}
"""

# Crawl settings
count = 0
limit = 100000
minstars = 999999
tempminstars = minstars
cursor = None

# Crawl loop
while count < limit:
  qstr = f"stars:<{minstars}"
  print("---")
  while True:
    try:
      qtime = time.time()
      result = client.run_query(query, {"cursor": cursor, "queryStr": qstr})
      print(f"Queried in {round(time.time() - qtime, 2)}s")
      break
    except:
      time.sleep(0.75)
  print(f"Temp Min Stars: {tempminstars} - Min Stas: {minstars}")
  if 'data' not in result or 'search' not in result['data']:
    break
  repos = result['data']['search']['nodes']
  data = [(repo['id'], repo['nameWithOwner'], repo['stargazerCount']) for repo in repos]
  if len(data) + count > limit:
    data = data[:(limit-count)]
  print(f"Data Length: {len(data)}")
  cur.executemany('''
            INSERT INTO repositories (repo_id, name, stars)
            VALUES (%s, %s, %s)
            ON CONFLICT (repo_id) DO UPDATE
            SET stars = EXCLUDED.stars, last_updated = CURRENT_TIMESTAMP;
        ''', data)
  cur.execute("SELECT COUNT(*) FROM repositories;")
  count = cur.fetchone()[0]
  print(f"Count: {count}")
  if count >= limit:
    break
  if not result['data']['search']['pageInfo']['hasNextPage']:
    minstars = tempminstars
    cursor = None
  else:
    tempminstars = repos[-1]['stargazerCount']
    cursor = result['data']['search']['pageInfo']['endCursor']
  # time.sleep(0.75)

conn.commit()
cur.close()
conn.close()