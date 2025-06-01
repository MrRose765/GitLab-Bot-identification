"""
Script to extract repositories from the GitLab API.

By default, it queries the /projects endpoint to get repositories in descending order of last activity.
"""

import requests
import pandas as pd
from tqdm import tqdm
import os


def query_repository_page(page, api_key=None):
    """
    Query a page of the /projects endpoint from the GitLab API to get repositories in descending order of last activity.
    """
    query = 'https://gitlab.com/api/v4/projects'
    response = requests.get(
        query,
        headers={'Private-Token': api_key} if api_key else {},
        params={
            'per_page': 100,  # Adjust the number of results per page as needed
            'page': page,
            'sort': 'desc',
            'order_by': 'updated_at'
        }
    )
    if response.ok:
        return response.json()
    else:
        print(f"Error while querying page {page}: {response.status_code}")
        return None

def parse_repository_data(repository):
    """
    Parse the repository data to extract relevant fields:
    - owner: The namespace path of the repository owner
    - project: The path of the repository
    - id: The ID of the repository
    - #stars: The number of stars the repository has
    """
    return {
        'owner': repository.get('namespace', {}).get('path', ''),
        'project': repository.get('path', ''),
        'id': repository.get('id', 0),
        '#stars': repository.get('star_count', 0)
    }

def extract_repositories(api_key=None, max_queries=1000, path='gitlab_repositories.csv'):
    """
    Extract active repositories from the GitLab API.
    """

    df_repo = None

    for page in tqdm(range(1, max_queries + 1), total=max_queries, desc="Extracting repositories"):
        repositories = query_repository_page(page, api_key)

        if repositories is None or len(repositories) == 0:
            print(f"No more repositories found on page {page}. Stopping extraction.")
            break

        for repository in repositories:
            repo_data = parse_repository_data(repository)
            if df_repo is not None and repo_data['id'] in df_repo['id'].values:
                # Skip if the repository is already in the DataFrame
                continue

            if df_repo is None:
                df_repo = pd.DataFrame([repo_data])
            else:
                df_repo = pd.concat([df_repo, pd.DataFrame([repo_data])], ignore_index=True)

            df_repo.to_csv(path, index=False)


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    key = os.getenv('GITLAB_API_KEY')

    # Get 10k repositories
    extract_repositories(api_key=key, max_queries=1000)







