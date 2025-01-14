import warnings
from datetime import datetime
from importlib.resources import files

from important_features import __stats, __convert_col_type
import pandas as pd
import requests.exceptions
from ghmap.mapping.action_mapper import ActionMapper
from ghmap.mapping.activity_mapper import ActivityMapper
from ghmap.utils import load_json_file
from rabbit import get_model, compute_confidence, check_ratelimit

QUERY_ROOT = "https://api.github.com"


def query_event_page(contributor, api_key, page):
    """
    Get the raw events of a contributor from the GitHub API on the given page.

    The query is `https://api.github.com/users/<contributor>/events?per_page=100&page=<page>`.
    """
    query = f'{QUERY_ROOT}/users/{contributor}/events?per_page=100&page={page}'
    headers = {}
    if api_key:
        headers['Authorization'] = f'token {api_key}'
    response = requests.get(query, headers=headers)

    if response.ok:
        # Return the events as a list of dictionaries
        return response.json()
    else:
        # TODO: Add better error handling
        print(f"Error while querying {contributor}: {response.status_code}")
        return []


def query_events(contributor, api_key, max_queries=3):
    """
    Query the events of a contributor from the GitHub API.
    A maximum of `max_queries` pages are queried where each page contains 100 events.
    """
    events = []
    for page in range(1, max_queries + 1):
        new_events = query_event_page(contributor, api_key, page)
        events.extend(new_events)

        if len(new_events) < 100:
            break
    return events


def query_user_type(contributor, api_key):
    """
    Query the type of contributor from the GitHub API.
    """
    query = f'{QUERY_ROOT}/users/{contributor}'
    if api_key:
        headers = {'Authorization': f'token {api_key}'}
    else:
        headers = {}
    response = requests.get(query, headers=headers)

    if response.ok:
        # Print the remaining number of queries
        reset_time = datetime.fromtimestamp(int(response.headers['X-RateLimit-Reset'])).strftime('%Y-%m-%d %H:%M:%S')
        print(f"Querying {contributor} : Remaining queries: {response.headers['X-RateLimit-Remaining']}. It will reset at {reset_time}")

        check_ratelimit(int(response.headers['X-RateLimit-Remaining']), int(response.headers['X-RateLimit-Reset']), 4)

        return response.json()['type']
    else:
        print(f"Error while querying {contributor}: {response.status_code}")
        return 'Invalid'


def events_to_activities(events):
    """
    Convert the events to activities using ghmap.

    args: A list of dictionaries corresponding to the events of a contributor

    returns: A list of dictionaries corresponding to the activities of a contributor
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


def activity_to_df(act):
    """
    Convert the activities to a DataFrame compatible with the RABBIT feature extractor.

    The returned DataFrame will have the following columns:
    - 'date'
    - 'activity'
    - 'contributor'
    - 'repository' (shape: 'owner/repo')

    args: A list of dictionaries corresponding to the activities of a contributor

    returns: A DataFrame with the activities of the contributor
    """
    activities_df = pd.DataFrame()
    for activity in act:
        new_row = pd.DataFrame([[
            activity['start_date'],
            activity['activity'],
            activity['actor']['login'],
            activity['repository']['name']
        ]], columns=['date', 'activity', 'contributor', 'repository'])
        activities_df = pd.concat([activities_df, new_row], ignore_index=True)
    activities_df['date'] = (pd.to_datetime(activities_df['date'], errors='coerce', format='%Y-%m-%dT%H:%M:%SZ')
                             .dt.tz_localize(None))
    return activities_df


def extract_features(df, contributor):
    """
    Extract the features from the activities of a user.
    It uses the same features as the RABBIT feature extractor but does not remove some features
    (NR, DCA_iqr, NAR_std, NTR_IQR, NCAR_median, NCAR_gini, DCAR_gini).

    args:
    - df: activity DataFrame with the columns 'date', 'activity', 'contributor' and 'repository (owner/repo)'

    returns: A DataFrame with the features extracted from the user's activities

    The features that are extracted are:
    - NA: number of activities,
    - NT: number of activity types,
    - NOR: number of owners of repositories,
    - *NR*: number of repositories,
    - ORR: Owner repository ratio,
    - DCA: time difference between consecutive activities (mean, median, std and gini, *IQR*),
    - NAR: number of activities per repository (mean, median, gini and IQR, *std*),
    - NTR: number of activity types per repository (mean, median, std and gini, *IQR),
    - NCAR: number of continuous activities in a repo (mean, std and IQR, *median*, *gini*),
    - DCAR: total time taken to perform consecutive activities in a repo (mean, median, std and IQR, *gini*),
    - DAAR: time taken to switch repos (mean, median, std, gini and IQR),
    - DCAT: time taken to switch activity type (mean, median, std, gini and IQR),
    - NAT: number of activities per type (mean, median, std, gini and IQR).
    """
    df['date'] = pd.to_datetime(df.date, errors='coerce', format='%Y-%m-%dT%H:%M:%S+00:00').dt.tz_localize(None)
    df[['owner', 'repo']] = df.repository.str.split('/', expand=True)

    # Extract features using RABBIT extractor
    df_feat = pd.json_normalize(__stats(df), sep='_')

    df_feat = (
        __convert_col_type(df_feat)
        .rename(columns={'feat_NA':'NA', 'feat_NT':'NT', 'feat_NOR':'NOR', 'feat_ORR':'ORR'})
        .sort_index()
        .set_index([[contributor]])
    )

    return df_feat


def predict_contributor(user, api_key, min_events=5, max_queries=3):
    """
    Predict if a user is a bot or not. If the user has less than `min_events` events, the prediction is 'Unknown'.

    args:
    - user: The username of the user to predict
    - API_KEY: The GitHub API key

    returns:
    - `contributor_type`: The type of the contributor ('Bot', 'Human' or 'Unknown')
    - `confidence`: The confidence of the prediction
    """
    raw_events = query_events(user, api_key, max_queries)
    if len(raw_events) < min_events:
        return 'Unknown', 0.0
    activities = events_to_activities(raw_events)
    df = activity_to_df(activities)

    df_feat = extract_features(df, user)

    model = get_model()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        proba = model.predict_proba(df_feat)
    contributor_type, confidence = compute_confidence(proba[0][1])

    return contributor_type, confidence


def make_predictions(contributors_df, query_user=True, min_events=5, max_queries=3, api_key=None):
    """
    Predict the type of contributor for each contributor in the DataFrame.

    args:
    - contributors_df: DataFrame with the contributors. It should have the column 'contributor'.
    - query_user: If True, query the type of the user from the GitHub API before predicting (default: True)
    - min_events: Minimum number of events to predict. If not met, prediction = Unknown (default: 5)
    - max_queries: Maximum number of queries to the GitHub API (default: 3)
    - API_KEY: GitHub API key. (Optional)

    returns: A Dataframe with two column : 'contributor', 'type' and 'confidence'

    """
    for contributor in contributors_df['contributor']:
        if query_user:
            contributor_type = query_user_type(contributor, api_key)
            contributors_df.loc[contributors_df['contributor'] == contributor, 'confidence'] = 1
            if contributor_type == 'Invalid':
                # User could not be found
                contributors_df.loc[contributors_df['contributor'] == contributor, 'type'] = contributor_type
                continue
            elif contributor_type == 'Bot':
                # User is already classified as a bot by GitHub
                contributors_df.loc[contributors_df['contributor'] == contributor, 'type'] = contributor_type
                continue
        contributor_type, confidence = predict_contributor(contributor, api_key, min_events, max_queries)
        # Add type and confidence next_to the contributor
        contributors_df.loc[contributors_df['contributor'] == contributor, 'type'] = contributor_type
        contributors_df.loc[contributors_df['contributor'] == contributor, 'confidence'] = confidence

    return contributors_df


if __name__ == '__main__':
    API_KEY = None

    contributors = pd.DataFrame({'contributor': ['MrRose765', 'Nephty', 'robodoo']})
    contributors = make_predictions(contributors, api_key=API_KEY)
    print(contributors)
