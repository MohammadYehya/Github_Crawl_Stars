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
    while True:
        try:
            print(f"Min Stars: {tempminstars}")
            result = client.run_query(query, {"cursor": cursor, "queryStr": qstr})
            break
        except:
          time.sleep(0.75)
    if 'data' not in result or 'search' not in result['data']:
        break
    repos = result['data']['search']['nodes']
    # for repo in repos:
    #     cur.execute('''
    #         INSERT INTO repositories (repo_id, name, stars)
    #         VALUES (%s, %s, %s)
    #         ON CONFLICT (repo_id) DO UPDATE
    #         SET stars = EXCLUDED.stars, last_updated = CURRENT_TIMESTAMP;
    #     ''', (repo['id'], repo['nameWithOwner'], repo['stargazerCount']))
    #     count += 1
    #     if count >= limit:
    #         break
    data = [(repo['id'], repo['nameWithOwner'], repo['stargazerCount']) for repo in repos]
    if len(data) + count > limit:
      data = data[:(limit-len(data)-count-1)]
    cur.executemany('''
              INSERT INTO repositories (repo_id, name, stars)
              VALUES (%s, %s, %s)
              ON CONFLICT (repo_id) DO UPDATE
              SET stars = EXCLUDED.stars, last_updated = CURRENT_TIMESTAMP;
          ''', )
    count += len(data)
    if count >= limit:
      break
    if not result['data']['search']['pageInfo']['hasNextPage']:
      minstars = tempminstars
      cursor = None
    else:
      tempminstars = repos[-1]['stargazerCount']
      cursor = result['data']['search']['pageInfo']['endCursor']
        
    time.sleep(0.75)

conn.commit()
cur.close()
conn.close()