"""
This script fetches events from users that are not yet in the features' dataset. (But in the dataset)

It then saves the events in a json file in the folder ../tests/gitlab_dataset/<origin>_events/<username>.json
"""

import json
import os
import pandas as pd
from tqdm import tqdm

from gitbot_utils.gl_api import GitLabManager

def fetch_and_save(manager, username, id, folder):
    """
    Fetch events for a given id and save them to a json file (<folder>/<username>.json).
    """
    events = manager.query_events(id)

    if not os.path.exists(folder):
        os.makedirs(folder)

    if events and len(events) >= manager.min_events:
        # Save events to json file
        with open(f"{folder}/{username}.json", "w") as f:
            json.dump(events, f, indent=4)
        return True
    else:
        print(f"No events found for {username}")
        return False


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()

    key = None
    gl_manager = GitLabManager(key, max_queries=3,
                                 before="2025-01-21", after="2024-10-21")

    skipped = []
    # Load the dataset
    df_features = pd.read_csv("../resources/data/gitlab/gitlab_glmap_features.csv")
    dataset = pd.read_csv("../resources/data/gitlab/dataset.csv")

    # Get users where username not yet in features
    dataset = dataset[~dataset['username'].isin(df_features['contributor'])]


    for i, row in tqdm(dataset.iterrows(), total=len(dataset), desc="Fetching events", unit="user"):
        folder = '../tests/gitlab_dataset/'
        if row['origin'] == 'human':
            folder += 'human_events'
        elif row['origin'] == 'bot-heuristic':
            folder += 'bot_heuristic_events'
        else:
            folder += 'github_common_events'
        # Fetch and save events
        res = fetch_and_save(gl_manager, row['username'], row['id'], folder)
        if not res:
            skipped.append(row['username'])

    # Save skipped users to a file
    with open("skipped_humans.txt", "w") as f:
        for user in skipped:
            f.write(f"{user}\n")
