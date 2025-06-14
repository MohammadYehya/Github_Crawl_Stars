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
page = 1

while count < limit:
  print(f"Fetching page {page} with cursor: {cursor}")
  check = True
  while check:
    try:
      result = client.run_query(query, {"cursor": cursor})
      check = False
    except:
      time.sleep(5)
      check = True
  repos = result['data']['search']['nodes']
  print(f"Fetched {len(repos)} repositories")

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
  print(f"Total collected so far: {count}")
  cursor = result['data']['search']['pageInfo']['endCursor']
  # if not result['data']['search']['pageInfo']['hasNextPage']:
  #     print("No more pages to fetch.")
  #     break
  page += 1
  time.sleep(1)  # be nice to the API

print(f"Final total repositories inserted/updated: {count}")

conn.commit()
cur.close()
conn.close()
