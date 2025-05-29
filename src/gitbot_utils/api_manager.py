import time
from abc import abstractmethod
from datetime import datetime

import numpy as np
import pandas as pd
# Have to rename to avoid the problem with double underscore.
from important_features import __stats as stats, __convert_col_type as convert_col_type


class APIManager:
    """
    Abstract class for an API manager.

    Attributes:
        api_key: The API key to use the API
        max_queries: The maximum number of pages to query
        min_events: The minimum number of events to query
    """

    def __init__(self, api_key, query_root, max_queries=3, min_events=5):
        self.api_key = api_key
        self.max_queries = max_queries
        self.min_events = min_events
        self.query_root = query_root

    @abstractmethod
    def _query_event_page(self, contributor, page):
        """
        Abstract method to query a page of events of a contributor from the API.

        Parameters:
            contributor: The username of the contributor
            page: The page number to query

        Returns:
            A list of dictionaries corresponding to the events of a contributor
            The headers of the response

        """
        pass

    def query_events(self, contributor):
        """
        Query the events of a contributor from the GitHub API.
        A maximum of `max_queries` pages are queried where each page contains 100 events.
        """
        events = []
        for page in range(1, self.max_queries + 1):
            new_events, headers = self._query_event_page(contributor, page)
            events.extend(new_events)
            if not self._check_events_left(new_events, headers):
                break
        return events

    # Function to check if there are events left
    @abstractmethod
    def _check_events_left(self, events, headers):
        """
        Abstract method to check if there are events left to query. Useful to adapt to the API used.

        Parameters:
            events: A list of dictionaries corresponding to the events of a contributor
            headers: The headers of the response

        Returns:
            True if there are events left, False otherwise
        """
        pass

    @staticmethod
    def wait_reset(reset_time):
        """
        Wait until the reset time of the API.

        Parameters:
            reset_time: The reset time of the API in the format '%Y-%m-%d %H:%M:%S'
        """
        # TODO: Check if we need a reset overhead time like in rabbit.
        reset_time = datetime.strptime(reset_time, '%Y-%m-%d %H:%M:%S')
        time_diff = (reset_time - datetime.now()).total_seconds()
        print(f"Waiting for {time_diff} seconds until the reset time.")
        time.sleep(time_diff)

    @abstractmethod
    def events_to_activities(self, events):
        """
        Abstract method to convert the events to activities.

        Parameters:
            events: A list of dictionaries corresponding to the events of a contributor

        Returns:
            A list of dictionaries corresponding to the activities of a contributor
        """
        pass

    @abstractmethod
    def _get_repo_owner(self, activity):
        """
        Abstract method to get the owner of the repository where the activity was done.

        Parameters:
            activity: A dictionary corresponding to the activity of a contributor

        Returns:
            str: The owner of the repository
        """
        pass

    def activity_to_df(self, activities):
        """
        Convert the activities to a DataFrame compatible with the RABBIT feature extractor.

        The returned DataFrame will have the following columns:
        - 'date'
        - 'activity'
        - 'contributor'
        - 'repository` (id)
        - 'owner`

        Parameters:
            activities: A list of dictionaries corresponding to the activities of a contributor

        Returns:
            A DataFrame with the columns 'date', 'activity', 'contributor' and 'repository'
        """
        activities_df = pd.DataFrame()
        for activity in activities:
            new_row = pd.DataFrame([[
                activity['start_date'],
                activity['activity'],
                activity['actor']['login'],
                activity['repository']['id']
            ]], columns=['date', 'activity', 'contributor', 'repository'])
            new_row['owner'] = self._get_repo_owner(activity)
            activities_df = pd.concat([activities_df, new_row], ignore_index=True)
        activities_df['date'] = (pd.to_datetime(activities_df['date'], errors='coerce', format='%Y-%m-%dT%H:%M:%SZ')
                                 .dt.tz_localize(None))

        return activities_df

    @staticmethod
    def extract_features(df, contributor):
        """
        Extract the features from the activities of a user.
        It uses the same features as the RABBIT feature extractor but does not remove some features
        (NR, DCA_iqr, NAR_std, NTR_IQR, NCAR_median, NCAR_gini, DCAR_gini).

        args:
        - df: activity DataFrame with the columns 'date', 'activity', 'contributor', 'repository' (id) and 'owner'

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
        features = ['NA', 'NT', 'NR','NOR','ORR',
                    'NAR_mean', 'NAR_median', 'NAR_std', 'NAR_gini', 'NAR_IQR',
                    'NAT_mean', 'NAT_median', 'NAT_std', 'NAT_gini', 'NAT_IQR',
                    'NCAR_mean', 'NCAR_median', 'NCAR_std', 'NCAR_gini', 'NCAR_IQR',
                    'NTR_mean', 'NTR_median', 'NTR_std', 'NTR_gini', 'NTR_IQR',
                    'DCAR_mean', 'DCAR_median', 'DCAR_std', 'DCAR_gini', 'DCAR_IQR',
                    'DAAR_mean', 'DAAR_median', 'DAAR_std', 'DAAR_gini', 'DAAR_IQR',
                    'DCA_mean', 'DCA_median', 'DCA_std', 'DCA_gini', 'DCA_IQR',
                    'DCAT_mean', 'DCAT_median', 'DCAT_std', 'DCAT_gini', 'DCAT_IQR',
                    ]

        df['date'] = pd.to_datetime(df.date, errors='coerce', format='%Y-%m-%dT%H:%M:%S+00:00').dt.tz_localize(None)

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


    def compute_features(self, contributor):
        """
        Compute the features of a contributor.
        """
        events = self.query_events(contributor)
        if len(events) < self.min_events:
            return None

        activities = self.events_to_activities(events)
        activities_df = self.activity_to_df(activities)
        features = self.extract_features(activities_df, contributor)
        return features