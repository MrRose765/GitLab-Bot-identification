import json
import os
import pandas as pd

from gitbot_utils.gl_api import GitLabManager


def compute_features(manager, user_events, username):
    activities = manager.events_to_activities(user_events)
    # Convert activities to DataFrame
    df = manager.activity_to_df(activities)
    # Extract features
    df_feat = manager._extract_features(df, username)
    return df_feat


if __name__ == '__main__':
    gl_manager = GitLabManager()
    file = 'gitlab_bot_features.csv'

    bots = pd.read_csv("src/resources/data/gitlab-dataset/bot_labelled.csv")

    df_feat = pd.DataFrame(columns=['contributor','label',
                      'NA', 'NT', 'NR', 'NOR', 'ORR',
                      'NAR_mean', 'NAR_median', 'NAR_std', 'NAR_gini', 'NAR_IQR',
                      'NAT_mean', 'NAT_median', 'NAT_std', 'NAT_gini', 'NAT_IQR',
                      'NCAR_mean', 'NCAR_median', 'NCAR_std', 'NCAR_gini', 'NCAR_IQR',
                      'NTR_mean', 'NTR_median', 'NTR_std', 'NTR_gini', 'NTR_IQR',
                      'DCAR_mean', 'DCAR_median', 'DCAR_std', 'DCAR_gini', 'DCAR_IQR',
                      'DAAR_mean', 'DAAR_median', 'DAAR_std', 'DAAR_gini', 'DAAR_IQR',
                      'DCA_mean', 'DCA_median', 'DCA_std', 'DCA_gini', 'DCA_IQR',
                      'DCAT_mean', 'DCAT_median', 'DCAT_std', 'DCAT_gini', 'DCAT_IQR',
                      ])
    for i, row in bots.iterrows():
        username = row['username']
        # Read events from json file
        if not os.path.exists(f"src/tests/gitlab_dataset/bot_events/{username}.json"):
            continue
        with open(f"src/tests/gitlab_dataset/bot_events/{username}.json", "r") as f:
            user_events = json.load(f)

        # Compute features
        features = compute_features(gl_manager, user_events, username)
        features['contributor'] = username
        features['label'] = row['label']

        df_feat = pd.concat([df_feat, features], ignore_index=True)


    # Save features to csv file
    df_feat.to_csv(file, index=False)




