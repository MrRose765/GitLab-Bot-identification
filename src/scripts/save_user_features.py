"""
For each user in the dataset that is not already in the features file:
- Load the user's events from a JSON file.
- Compute features using the GitLabManager.
- Save the features in the features file.
"""

import json
import os

import pandas as pd
from tqdm import tqdm

from gitbot_utils.gl_api import GitLabManager


def compute_features(manager, user_events, username):
    activities = manager.events_to_activities(user_events)
    # Convert activities to DataFrame
    df = manager.activity_to_df(activities)
    # Extract features
    df_feat = manager.extract_features(df, username)
    return df_feat


if __name__ == '__main__':
    gl_manager = GitLabManager()
    file = 'gitlab_features_glmap.csv'

    df_features = pd.read_csv("../resources/data/gitlab/gitlab_glmap_features.csv")
    dataset_bot = pd.read_csv("../resources/data/gitlab/dataset.csv")

    # Get bots where username not in df_features
    dataset = dataset_bot[~dataset_bot['username'].isin(df_features['contributor'])]

    columns = ['contributor', 'label', 'origin',
               'NA', 'NT', 'NR', 'NOR', 'ORR',
               'NAR_mean', 'NAR_median', 'NAR_std', 'NAR_gini', 'NAR_IQR',
               'NAT_mean', 'NAT_median', 'NAT_std', 'NAT_gini', 'NAT_IQR',
               'NCAR_mean', 'NCAR_median', 'NCAR_std', 'NCAR_gini', 'NCAR_IQR',
               'NTR_mean', 'NTR_median', 'NTR_std', 'NTR_gini', 'NTR_IQR',
               'DCAR_mean', 'DCAR_median', 'DCAR_std', 'DCAR_gini', 'DCAR_IQR',
               'DAAR_mean', 'DAAR_median', 'DAAR_std', 'DAAR_gini', 'DAAR_IQR',
               'DCA_mean', 'DCA_median', 'DCA_std', 'DCA_gini', 'DCA_IQR',
               'DCAT_mean', 'DCAT_median', 'DCAT_std', 'DCAT_gini', 'DCAT_IQR',
               ]
    df_feat = pd.DataFrame(columns=columns)

    # tqdm with iterrows
    for i, row in tqdm(dataset.iterrows(), total=len(dataset), desc="Processing users", unit="user"):
        row['origin'] = 'bot-heuristic'
        username = row['username']
        path = '../tests/gitlab_dataset/'
        if row['origin'] == 'human':
            path += f'human_events/{username}.json'
        elif row['origin'] == 'bot-heuristic':
            path += f'bot_heuristic_events/{username}.json'
        else:
            path += f'github_common_events/{username}.json'

        if not os.path.exists(path):
            print(f"File {path} does not exist for user {username}. Skipping...")
            continue

        with open(path, "r") as f:
            user_events = json.load(f)

        # Compute features
        features = compute_features(gl_manager, user_events, username)
        features['contributor'] = username
        features['label'] = row['label']
        features['origin'] = row['origin']
        # Reorder columns to match the original DataFrame
        features = features[columns]

        if df_feat.empty:
            df_feat = features
        else:
            df_feat = pd.concat([df_feat, features], ignore_index=True)

    # Save features to csv file
    df_feat.to_csv(file, index=False)
