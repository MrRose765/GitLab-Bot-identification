import json
import warnings

import numpy as np
import pandas as pd
from ExtractEvent import unpackJson
from GenerateActivities import activity_identification
from important_features import __stats as stats, __convert_col_type as convert_col_type
from rabbit import compute_confidence, get_model


def _events_to_activities(raw_events):
    """
    Convert the events to activities and identify the activity type
    """
    raw_events = unpackJson(raw_events)
    df_events = pd.DataFrame.from_dict(raw_events, orient='columns')
    df_events['created_at'] = pd.to_datetime(df_events.created_at, errors='coerce',
                                                 format='%Y-%m-%dT%H:%M:%SZ').dt.tz_localize(None)
    df_events = df_events.sort_values(by='created_at')

    return activity_identification(df_events)

def _extract_features(df, contributor):
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
    features = ['NA', 'NT', 'NOR', 'ORR',
              'DCA_mean', 'DCA_median', 'DCA_std', 'DCA_gini',
              'NAR_mean', 'NAR_median', 'NAR_gini', 'NAR_IQR',
              'NTR_mean', 'NTR_median', 'NTR_std', 'NTR_gini',
              'NCAR_mean', 'NCAR_std', 'NCAR_IQR',
              'DCAR_mean', 'DCAR_median', 'DCAR_std', 'DCAR_IQR',
              'DAAR_mean', 'DAAR_median', 'DAAR_std', 'DAAR_gini', 'DAAR_IQR',
              'DCAT_mean', 'DCAT_median', 'DCAT_std', 'DCAT_gini', 'DCAT_IQR',
              'NAT_mean', 'NAT_median', 'NAT_std', 'NAT_gini', 'NAT_IQR']

    df['date'] = pd.to_datetime(df.date, errors='coerce', format='%Y-%m-%dT%H:%M:%S+00:00').dt.tz_localize(None)
    df[['owner', 'repo']] = df.repository.str.split('/', expand=True)

    # Extract features using RABBIT extractor
    df_feat = pd.json_normalize(stats(df), sep='_')

    # Add column 'NR' for Number of Repositories
    df_feat['NR'] = np.int64(df['repository'].nunique())

    df_feat = (
        convert_col_type(df_feat)
        .rename(columns={'feat_NA':'NA', 'feat_NT':'NT', 'feat_NOR':'NOR', 'feat_ORR':'ORR'})
        [features] # Reorder the columns
        .sort_index()
        .set_index([[contributor]])
    )

    return df_feat

def extract_bimbas_feature(raw_events, contr):
    """
    Convert the events to activities and extract the features using RABBIT feature extractor

    Parameters:
        raw_events: A list of dictionaries corresponding to the events of a contributor
        contr: The contributor name

    Returns:
        A DataFrame with the features extracted from the user's activities
    """
    # Use the activity mapping of bimbas (defined in this file)
    activity_df = _events_to_activities(raw_events)

    df_feat = _extract_features(activity_df, contr)
    # Set index name as contributor
    df_feat.index.name = 'contributor'

    return df_feat

def predict(df_feat):
    """
    Predict the type of the user based on its features

    Returns:
        A tuple with the contributor type and the confidence
    """
    model = get_model()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        proba = model.predict_proba(df_feat)
    return compute_confidence(proba[0][1])


def predict_user(events):
    """
    Predict the type of the user based on its events

    Parameters:
        events: A list of dictionaries corresponding to the events of a contributor

    Returns:
        A tuple with the contributor type and the confidence
    """
    df_features = extract_bimbas_feature(events, 'contributor')
    return predict(df_features)

if __name__ == '__main__':
    csv_file = 'events.json'

    with open(csv_file, 'r') as file:
        events = json.load(file)

    contributor_type, conf = predict_user(events)
    print(f"Contributor type: {contributor_type}, Confidence: {conf}")
