from datetime import datetime
from importlib.resources import files

import pandas as pd
import requests
from ExtractEvent import unpackJson
from GenerateActivities import activity_identification
from ghmap.mapping.action_mapper import ActionMapper
from ghmap.mapping.activity_mapper import ActivityMapper
from ghmap.utils import load_json_file
from .api_manager import APIManager


class GitHubManager(APIManager):

    def __init__(self, api_key=None, max_queries=3, min_events=5, ghmap=True):
        super().__init__(api_key, max_queries, min_events)
        self.ghmap = ghmap
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

    @staticmethod
    def __rabbit_activity_mapping(events):
        raw_events = unpackJson(events)
        df_events = pd.DataFrame.from_dict(raw_events, orient='columns')
        df_events['created_at'] = pd.to_datetime(df_events.created_at, errors='coerce',
                                                 format='%Y-%m-%dT%H:%M:%SZ').dt.tz_localize(None)
        df_events = df_events.sort_values(by='created_at')

        return activity_identification(df_events)

    @staticmethod
    def __ghmap_activity_mapping(events):
        # Step 1: Event to Action Mapping
        event_to_action_mapping_file = files("gitbot_utils").joinpath("config", "event_to_action.json")
        action_mapping = load_json_file(event_to_action_mapping_file)
        action_mapper = ActionMapper(action_mapping)

        actions = action_mapper.map(events)

        # Step 2: Actions to Activities Mapping
        action_to_activity_mapping_file = files("gitbot_utils").joinpath("config", "action_to_activity.json")
        activity_mapping = load_json_file(action_to_activity_mapping_file)
        activity_mapper = ActivityMapper(activity_mapping)

        activities = activity_mapper.map(actions)

        return activities

    def events_to_activities(self, events):
        """
        Convert the events to activities using ghmap.

        Parameters:
            events: A list of dictionaries corresponding to the events of a contributor

        Returns:
            A list of dictionaries corresponding to the activities of a contributor
        """
        if self.ghmap:
            return self.__ghmap_activity_mapping(events)
        else:
            return self.__rabbit_activity_mapping(events)


if __name__ == '__main__':
    import os
    from dotenv import load_dotenv
    load_dotenv()

    KEY = os.getenv('GITHUB_API_KEY')
    contributor = 'MrRose765'
    gh_api = GitHubManager(KEY)

    features = gh_api.compute_features(contributor)
    print(features)
