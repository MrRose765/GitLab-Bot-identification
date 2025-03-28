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
            return response.json(), response.headers
        else:
            print(f"Error while querying {contributor}: {response.status_code}")
            return []

    def _check_events_left(self, events, headers):
        """
        Check if there are events left to query from the GitHub API.
        """
        return len(events) == 100

    def _get_repo_owner(self, activity):
        """
        Get the owner of the repository where the activity took place.
        """
        return activity['repository']['name'].split('/')[0]

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
            query_remaining = int(response.headers['X-RateLimit-Remaining'])
            if query_remaining < self.max_queries:
                reset_time = (datetime.fromtimestamp(int(response.headers['X-RateLimit-Reset']))
                    .strftime('%Y-%m-%d %H:%M:%S'))
                self.wait_reset(reset_time)

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
    import model_utils as mod

    KEY = None
    contributor = 'MrRose765'
    gh_api = GitHubManager(KEY)

    features = gh_api.compute_features(contributor)

    model = mod.load_model("resources/models/bimbas.joblib")
    label, confidence = mod.predict_contributor(features, model)
    print(f"Contributor {contributor} is a {label} with confidence {confidence}")