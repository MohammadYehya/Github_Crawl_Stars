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
    print(f"Page {page}, Cursor: {cursor}")
    result = client.run_query(query, {"cursor": cursor})

    if 'data' not in result or 'search' not in result['data']:
        print("Unexpected response format:", result)
        break

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

    print(f"Total collected: {count}")
    if not result['data']['search']['pageInfo']['hasNextPage']:
        print("No more pages to fetch.")
        break

    cursor = result['data']['search']['pageInfo']['endCursor']
    page += 1
    time.sleep(1)

print(f"Crawl finished. Inserted {count} repositories.")

conn.commit()
cur.close()
conn.close()