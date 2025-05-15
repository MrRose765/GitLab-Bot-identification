from datetime import datetime
from importlib.resources import files

import requests
from ghmap.mapping.action_mapper import ActionMapper
from ghmap.mapping.activity_mapper import ActivityMapper
from ghmap.utils import load_json_file

from .api_manager import APIManager


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

            self.repo_mapping = {}

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
                return [], response.headers

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

        def query_user_info(self, contributor):
            """
            Query the information of contributor from the GitLab API. (ID, username, name, state, ...)
            """
            query = f'{self.query_root}/users?username={contributor}'
            headers = {}
            if self.api_key:
                headers['Private-Token'] = self.api_key
            response = requests.get(query, headers=headers)

            if response.ok:
                return response.json()
            else:
                print(f"Error while querying {contributor}: {response.status_code}")
                return None

        def _query_repo_info(self, project_id):
            """
            Query the information of a project from the GitLab API.
            """
            query = f'{self.query_root}/projects/{project_id}'
            headers = {}
            if self.api_key:
                headers['Private-Token'] = self.api_key
            response = requests.get(query, headers=headers)

            if response.ok:
                return response.json()
            else:
                print(f"Error while querying {project_id}: {response.status_code}")
                return None

        def _get_repo_owner(self, activity):
            """
            Get the owner of the repository where the activity was done.
            """
            project_id = activity['repository']['id']
            if project_id in self.repo_mapping:
                return self.repo_mapping[project_id]

            project_info = self._query_repo_info(project_id)
            if project_info:
                # Can be a user or a group (ex: gitlab-org)
                owner = project_info['namespace']['path']
                self.repo_mapping[project_id] = owner
                return owner

        def events_to_activities(self, events):
            """
            Convert the events to activities using glmap.

            Parameters:
                events: A list of dictionaries corresponding to the events of a contributor
            """
            # Step 1: Event to Action Mapping
            event_to_action_file = files("gitbot_utils").joinpath("config", "gl_event_to_action.json")
            action_mapping = load_json_file(event_to_action_file)
            action_mapper = ActionMapper(action_mapping)

            actions = action_mapper.map(events)

            # Step 2: Action to Activity Mapping
            action_to_activity_file = files("gitbot_utils").joinpath("config", "gl_action_to_activity.json")
            activity_mapping = load_json_file(action_to_activity_file)
            activity_mapper = ActivityMapper(activity_mapping)

            activities = activity_mapper.map(actions)

            return activities


if __name__ == '__main__':
    import os
    from dotenv import load_dotenv
    load_dotenv()

    user = 'louciole'
    api_key = os.getenv('GITLAB_API_KEY')
    gl_manager = GitLabManager(api_key,  before="2025-01-21", after="2024-10-21")
    #id = gl_manager.query_user_info(user)[0]['id']
    # pretty print the response
    #print(id)

    # project_info = gl_manager._query_repo_info(278964)

    # Predict the type of contributor
    features = gl_manager.compute_features(user)
    print(features)