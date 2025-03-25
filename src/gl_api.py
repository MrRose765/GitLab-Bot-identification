from datetime import datetime

import requests

from src.api_manager import APIManager


class GitLabManager(APIManager):
        def __init__(self, api_key=None, max_queries=3, before=None, after=None):
            """
            Initialize the GitLab API manager.

            Parameters:
                api_key: The API key to access the GitLab API
                max_queries: The maximum number of queries to be made to the GitLab API
                before: The date before which events are queried. (Format: YYYY-MM-DD)
                after: The date after which events are queried. (Format: YYYY-MM-DD)
            """
            super().__init__(api_key, max_queries)
            self.query_root = 'https://gitlab.com/api/v4'
            # Query parameters
            self.before = "&before=" + before if before else ""
            self.after = "&after=" + after if after else ""

        def _query_event_page(self, contributor, page):
            """
            Query a page of events of a contributor from the GitLab API.
            """
            query = f'{self.query_root}/users/{contributor}/events?per_page=100&page={page}{self.before}{self.after}'
            headers = {}
            if self.api_key:
                headers['Private-Token'] = self.api_key
            response = requests.get(query, headers=headers)

            if response.ok:
                # Return the events as a list of dictionaries
                return response.json(), response.headers
            elif response.status_code == 429:
                print("Rate limit exceeded", end=' ')
                reset_time = (datetime.fromtimestamp(int(response.headers['RateLimit-Reset']))
                              .strftime('%Y-%m-%d %H:%M:%S'))
                self.wait_reset(reset_time)
            else:
                print(f"Error while querying {contributor}: {response.status_code}")
                return []

        def _check_events_left(self, events, headers):
            """
            Check if there are events left to query from the GitLab API.
            """
            if 'X-Next-Page' in headers or len(events) == 100:
                return True
            return False

        def query_user_type(self, contributor_id):
            """
            Query the type of contributor from the GitLab API.
            """
            if not self.api_key:
                print("API key is required to query user type.")
                return None
            query = f'{self.query_root}/users/{contributor_id}'
            headers = {}
            if self.api_key:
                headers['Private-Token'] = self.api_key
            response = requests.get(query, headers=headers)

            if response.ok:
                return response.json()['bot']
            else:
                print(f"Error while querying {contributor_id}: {response.status_code}")
                return None

        def query_user_id(self, contributor):
            """
            Query the id of contributor from the GitLab API.
            """
            query = f'{self.query_root}/users?username={contributor}'
            headers = {}
            if self.api_key:
                headers['Private-Token'] = self.api_key
            response = requests.get(query, headers=headers)

            if response.ok:
                return response.json()[0]['id']
            else:
                print(f"Error while querying {contributor}: {response.status_code}")
                return None

        def events_to_activities(self, events):
            """
            Convert the events to activities using glmap.

            Parameters:
                events: A list of dictionaries corresponding to the events of a contributor
            """
            # Error if called
            raise NotImplementedError("Method not implemented")

if __name__ == '__main__':
    user = 'Louciole'
    api_key = None
    gl_manager = GitLabManager(api_key, before="2024-11-30", after="2024-11-28")
    id = gl_manager.query_user_id(user)
    # pretty print the response
    print(id)

    events = gl_manager.query_events(user)
    print(f"Number of events: {len(events)}")
    for event in events:
        print(event['created_at'])