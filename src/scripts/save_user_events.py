import json
import os
import pandas as pd
from tqdm import tqdm

from gitbot_utils.gl_api import GitLabManager

def fetch_and_save(manager, username, folder):
    """
    Fetch events for a given username and save them to a CSV file.
    """
    events = manager.query_events(username)
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

    key = os.getenv('GITLAB_API_KEY')
    gl_manager = GitLabManager(api_key=key, max_queries=3, before="2025-01-21", after="2024-10-21")
    folder = '../tests/gitlab_dataset/bot_events'

    skipped = []
    # Load the dataset
    dataset = pd.read_csv("../resources/data/gitlab-dataset/bot_labelled.csv")

    for user in tqdm(dataset['username'], desc="Fetching events", unit="user"):
        # Fetch and save events
        res = fetch_and_save(gl_manager, user, folder)
        if not res:
            skipped.append(user)

    # Save skipped users to a file
    with open("skipped_users.txt", "w") as f:
        for user in skipped:
            f.write(f"{user}\n")
