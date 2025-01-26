from datetime import datetime

import requests

from src.api_manager import APIManager


class GitLabManager(APIManager):
        def __init__(self, api_key=None, max_queries=3):
            super().__init__(api_key, max_queries)
            self.query_root = 'https://gitlab.com/api/v4'

        def _query_event_page(self, contributor, page):
            """
            Query a page of events of a contributor from the GitLab API.
            """
            query = f'{self.query_root}/users/{contributor}/events?per_page=100&page={page}'
            headers = {}
            if self.api_key:
                headers['Private-Token'] = self.api_key
            response = requests.get(query, headers=headers)

            if response.ok:
                # Return the events as a list of dictionaries
                return response.json()
            elif response.status_code == 429:
                print("Rate limit exceeded", end=' ')
                reset_time = (datetime.fromtimestamp(int(response.headers['RateLimit-Reset']))
                              .strftime('%Y-%m-%d %H:%M:%S'))
                self.wait_reset(reset_time)
            else:
                print(f"Error while querying {contributor}: {response.status_code}")
                return []


        def events_to_activities(self, events):
            """
            Convert the events to activities using glmap.

            Parameters:
                events: A list of dictionaries corresponding to the events of a contributor
            """
            # Error if called
            raise NotImplementedError("Method not implemented")

if __name__ == '__main__':
    user = 'louciole'
    gl_manager = GitLabManager()
    events = gl_manager.query_events(user)
    print(f"Number of events: {len(events)}")
    print(events[0])