from crawler.github_client import GitHubClient
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
query ($cursor: String) {
  search(query: "stars:>0", type: REPOSITORY, first: 100, after: $cursor) {
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

cursor = None
count = 0
limit = 100000

while count < limit:
    result = client.run_query(query, {"cursor": cursor})
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
    cursor = result['data']['search']['pageInfo']['endCursor']
    if not result['data']['search']['pageInfo']['hasNextPage']:
        break
    time.sleep(1)  # be nice to the API

conn.commit()
cur.close()
conn.close()
