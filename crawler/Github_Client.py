import requests
import time

class GitHubClient:
    def __init__(self, token):
        self.api_url = 'https://api.github.com/graphql'
        self.headers = {
            'Authorization': f'bearer {token}'
        }

    def run_query(self, query, variables=None):
        while True:
            response = requests.post(
                self.api_url,
                json={'query': query, 'variables': variables},
                headers=self.headers
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 403 and 'X-RateLimit-Reset' in response.headers:
                reset_time = int(response.headers['X-RateLimit-Reset'])
                wait = reset_time - int(time.time()) + 5
                print(f"Rate limit hit. Waiting {wait} seconds...")
                time.sleep(max(wait, 0))
            else:
                raise Exception(f"Query failed: {response.text}")