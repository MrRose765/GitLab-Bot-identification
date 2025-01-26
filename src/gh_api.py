from datetime import datetime
from importlib.resources import files

import rabbit as rb
from ghmap.mapping.action_mapper import ActionMapper
from ghmap.mapping.activity_mapper import ActivityMapper
from ghmap.utils import load_json_file

from src.api_manager import APIManager
import requests

class GitHubManager(APIManager):

    def __init__(self, api_key=None, max_queries=3):
        super().__init__(api_key, max_queries)
        self.query_root = 'https://api.github.com'

    def _query_event_page(self, contributor, page):
        """
        Query a page of events of a contributor from the GitHub API.
        """
        query = f'{self.query_root}/users/{contributor}/events?per_page=100&page=<page>'
        headers = {}
        if self.api_key:
            headers['Authorization'] = f'token {self.api_key}'
        response = requests.get(query, headers=headers)

        if response.ok:
            # Return the events as a list of dictionaries
            return response.json()
        else:
            print(f"Error while querying {contributor}: {response.status_code}")
            return []

    def query_user_type(self, contributor):
        """
        Query the type of contributor from the GitHub API.
        """
        query = f'{self.query_root}/users/{contributor}'
        headers = {}
        if self.api_key:
            headers['Authorization'] = f'token {self.api_key}'
        response = requests.get(query, headers=headers)

        if response.ok:
            # Print the remaining number of queries
            reset_time = datetime.fromtimestamp(int(response.headers['X-RateLimit-Reset'])).strftime(
                '%Y-%m-%d %H:%M:%S')
            print(
                f"Querying {contributor} : Remaining queries: {response.headers['X-RateLimit-Remaining']}. It will reset at {reset_time}")

            rb.check_ratelimit(int(response.headers['X-RateLimit-Remaining']), int(response.headers['X-RateLimit-Reset']),
                            4)

            return response.json()['type']
        else:
            print(f"Error while querying {contributor}: {response.status_code}")
            return 'Invalid'


    def events_to_activities(self, events):
        """
        Convert the events to activities using ghmap.

        Parameters:
            events: A list of dictionaries corresponding to the events of a contributor

        Returns:
            A list of dictionaries corresponding to the activities of a contributor
        """

        # Step 1: Event to Action Mapping
        event_to_action_mapping_file = files("src").joinpath("resources/config", "event_to_action.json")
        action_mapping = load_json_file(event_to_action_mapping_file)
        action_mapper = ActionMapper(action_mapping)

        actions = action_mapper.map(events)

        # Step 2: Actions to Activities Mapping
        action_to_activity_mapping_file = files("src").joinpath("resources/config", "action_to_activity.json")
        activity_mapping = load_json_file(action_to_activity_mapping_file)
        activity_mapper = ActivityMapper(activity_mapping)

        activities = activity_mapper.map(actions)

        return activities

if __name__ == '__main__':
    KEY = None
    gh_api = GitHubManager(KEY)

    # Test the query_events method
    raw_events = gh_api.query_events('MrRose765')
    print(len(raw_events))
    print(raw_events[0])

    features = gh_api.compute_features('MrRose765')
    print(features)