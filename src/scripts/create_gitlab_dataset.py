"""
This script contains the functions used to extract bot and human contributors from GitLab repositories.

For bots, it queries the members of each repository from a list and applies a heuristic to determine if they are bots.

For humans, it queries the contributors of each repository based on their events and applies a heuristic to filter out bots.

Then, two models (BIMBIS and BIMBAS) are used to predict the type of contributors (Bot or Human) based on their activity features.
"""

import os
import random

import pandas as pd
import requests
from dotenv import load_dotenv

import gitbot_utils.model_utils as mod
from gitbot_utils.gl_api import GitLabManager

load_dotenv()


def bot_heuristic(username, name):
    """
    Heuristic to determine if a contributor is a bot based on their username.
    """
    return (
            any(bot_keyword in username for bot_keyword in ['bot', 'ci', 'io', 'token'])
            or
            any(bot_keyword in name for bot_keyword in ['bot', 'ci', 'io', 'token'])
    )


class ContributorManager(GitLabManager):
    """
    Manager specialized in querying contributors and members of GitLab repositories.
    """

    def _query_member_page(self, project_id, page):
        query = f'{self.query_root}/projects/{project_id}/members/all'
        response = requests.get(
            query,
            headers={'Private-Token': self.api_key} if self.api_key else {},
            params={'per_page': 100, 'page': page}
        )

        if response.ok:
            return response.json()
        else:
            print(f"Error while querying {project_id}: {response.status_code}")
            return None

    def _query_repo_event_page(self, project_id, page):
        query = f'{self.query_root}/projects/{project_id}/events'
        response = requests.get(
            query,
            headers={'Private-Token': self.api_key} if self.api_key else {},
            params={'per_page': 100, 'page': page}
        )

        if response.ok:
            return response.json(), response.headers
        else:
            print(f"Error while querying {project_id}: {response.status_code}")
            return [], response.headers

    def query_repo_members(self, project_id):
        """
        Query all members of a project. (/projects/{project_id}/members/all)
        """
        all_members = []
        page = 1
        while True:
            members = self._query_member_page(project_id, page)
            if not members:
                break
            all_members.extend(members)
            page += 1
        return all_members

    def query_repo_contributors(self, project_id, min_contributors=10):
        """
        Query human contributors of a project based on their events.

        This method will:
        1. Query the events of the project.
        2. Extract the authors of the events and apply a heuristic to filter out bots.
        3. Stop querying new pages when we have enough contributors or when there are no more events.
        4. Return a list of contributors with their ID, username, and name.
        """
        contributors = []
        known_usernames = set()

        for i in range(1, self.max_queries + 1):
            events, headers = self._query_repo_event_page(project_id, i)
            if not events:
                break

            for event in events:
                if 'author' not in event:
                    continue
                username = event['author']['username']
                is_bot = bot_heuristic(username, event['author'].get('name', ''))
                if username in known_usernames or not is_bot:
                    continue

                contributors.append({
                    'id': event['author']['id'],
                    'username': username,
                    'name': event['author'].get('name', 'Unknown')
                })
                known_usernames.add(username)
            if len(contributors) >= min_contributors:
                # If we have enough contributors, we can stop querying
                break
        return list(contributors)


def analyse_contributor(contributor, gitlab_manager: GitLabManager, bimbis, bimbas):
    """
    Analyse a contributor's activity and return a dictionary with the following information:
    - username: the username of the contributor. (identification of the contributor)
    - name: the name of the contributor. (Display name of the contributor)
    - nb_activity: The number of activities mapped with glmap.
    - bimbis_label: The label predicted by the BIMBIS model (Bot or Human).
    - bimbis_conf: The confidence of the BIMBIS model prediction (between 0 and 1).
    - bimbas_label: The label predicted by the BIMBAS model (Bot or Human).
    - bimbas_conf: The confidence of the BIMBAS model prediction (between 0 and 1).
    - label: Label of the two models or 'Unknown' if the two models disagree.
    """

    features = gitlab_manager.compute_features(contributor['id'])
    if features is None:
        return None
    label_bimbis, conf_bimbis = mod.predict_contributor(features, model=bimbis)
    label_bimbas, conf_bimbas = mod.predict_contributor(features, model=bimbas)

    if label_bimbas != label_bimbis:
        label = 'Unknown'
    else:
        label = label_bimbis

    return {
        "username": contributor['username'],
        "name": contributor['name'],
        'nb_activity': int(features['NA'].iloc[0]),
        "bimbis_label": label_bimbis,
        "bimbis_conf": conf_bimbis,
        "bimbas_label": label_bimbas,
        "bimbas_conf": conf_bimbas,
        "label": label
    }


def extract_bot_users(repository, contributor_manager, bimbis, bimbas):
    """
    Extract bot users from the active repositories.
    To do so, we will fetch the members of the repository and apply a heuristic to determine if they are bots.

    We will :
    1. For each repository, get the members.
    2. Apply a heuristic to determine if the member is a bot (if username/name contains 'bot', 'io' or 'ci').
    3. Predict the type of contributors using BIMBIS and BIMBAS models. (Avoid false positives in the dataset)
    """
    members = contributor_manager.query_repo_members(repository['id'])

    # Keep members that are bots
    bot_members = [member for member in members if bot_heuristic(member['username'], member.get('name', ''))]

    results = [
        analyse_contributor(bot, contributor_manager, bimbis, bimbas)
        for bot in bot_members
    ]

    return pd.DataFrame(results)


def extract_human_users(repository, contributor_manager, bimbis, bimbas, min_contributors=10):
    """
    Extract human from the active repositories.
    To do so, we will fetch their last events and analyse the authors.

    We will :
    1. For each repository, get 10 contributors.
    2. Get the author of each event
    3. Skip the author if he has 'bot'/'ci'/'io' in its name or username
    4. Predict the type of contributors using BIMBIS and BIMBAS models. (Avoid false negatives in the dataset)
    """

    contributors = contributor_manager.query_repo_contributors(repository['id'], min_contributors)
    print(f"Number of contributors found: {len(contributors)}")

    if len(contributors) > min_contributors:
        # Select randomly min_contributors contributors
        contributors = random.sample(contributors, min_contributors)

    results = []
    for contributor in contributors:
        info = analyse_contributor(contributor, contributor_manager, bimbis, bimbas)
        if info is None:
            continue
        info['repository'] = repository['id']
        results.append(info)

    return pd.DataFrame(results)


if __name__ == '__main__':
    KEY = os.getenv("GITLAB_API_KEY")
    manager = ContributorManager(KEY, max_queries=3,
                                 before="2025-01-21", after="2024-10-21")
    bimbis = mod.load_model("../resources/models/bimbis.joblib")
    bimbas = mod.load_model("../resources/models/bimbas.joblib")

    repositories = pd.read_csv("../resources/data/gitlab/gitlab_repositories.csv")
    repositories = repositories.sort_values(by='#stars', ascending=True).reset_index(drop=True)

    start = 1 - 1

    df_result = None
    for index, row in repositories.iloc[start:].iterrows():
        repo_name = row['repo']

        print(f"=============== {repo_name} ===============")
        repo_df = extract_human_users(row, manager, bimbis, bimbas)

        if repo_df.empty:
            print(f"No active contributors found for {repo_name}. Skipping...")
            continue

        print(f"Number of bot contributors found: {len(repo_df[repo_df['label'] == 'Bot'])}")
        print(f"Number of human contributors found: {len(repo_df[repo_df['label'] == 'Human'])}")
        print(f"Number of unknown contributors found: {len(repo_df[repo_df['label'] == 'Unknown'])}")

        # Concat with current df or create new if it doesn't exist
        if df_result is None:
            df_result = repo_df
        else:
            df_result = pd.concat([df_result, repo_df], ignore_index=True)

        # Save file
        df_result.to_csv("../resources/data/gitlab/oui.csv", index=False)
