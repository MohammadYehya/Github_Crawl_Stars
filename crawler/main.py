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

# Split function
def split_range(r):
    s, e = map(int, r.split('..'))
    if e - s <= 1:
        return []
    m = (s + e) // 2
    return [f"{s}..{m}", f"{m+1}..{e}"]

# Initial slice setup
star_ranges = [(90001, 100000), (80001, 90000), (70001, 80000), (60001, 70000), (50001, 60000), (40001, 50000), (30001, 40000), (20001, 30000), (10001, 20000),
               (9001, 10000), (8001, 9000), (7001, 8000), (6001, 7000), (5001, 6000), (4001, 5000), (3001, 4000), (2001, 3000), (1001, 2000),
               (901, 1000), (801, 900), (701, 800), (601, 700), (501, 600), (401, 500), (301, 400), (201, 300), (101, 200),
               (91, 100), (81, 90), (71, 80), (61, 70), (51, 60), (41, 50), (31, 40), (21, 30), (11, 20), (1, 10)]

slices = [f"stars:{s}..{e}" for s, e in star_ranges]

# Crawl settings
count = 0
limit = 100000

# Crawl loop
while slices and count < limit:
    slice_q = slices.pop(0)
    cursor = None

    for _ in range(10):
        while True:
            try:
                print(f"Requesting slice: {slice_q}, cursor: {cursor}")
                result = client.run_query(query, {"cursor": cursor, "queryStr": slice_q})
                break
            except:
              time.sleep(5)
        if 'data' not in result or 'search' not in result['data']:
            break
        repos = result['data']['search']['nodes']
        for repo in repos:
            cur.execute('''
                INSERT INTO repositories (repo_id, name, stars)
                VALUES (%s, %s, %s)
                ON CONFLICT (repo_id) DO UPDATE
                SET stars = EXCLUDED.stars, last_updated = CURRENT_TIMESTAMP;
            ''', (repo['id'], repo['nameWithOwner'], repo['stargazerCount']))
            count += 1
            if count >= limit:
                break
        if not result['data']['search']['pageInfo']['hasNextPage']:
            break
        cursor = result['data']['search']['pageInfo']['endCursor']
        time.sleep(1)

conn.commit()
cur.close()
conn.close()