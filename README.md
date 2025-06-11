# GitLab Bot Identification


This repository contains the source code and resources developed as part of my master's thesis in Computer Science 
at the [University of Mons](https://web.umons.ac.be/en/university/), conducted within the Software Engineering Lab of the Faculty of Science.

The thesis is entitled *"Study of the Transferability of the BIMBAS Bot Detection Model between GitHub and GitLab"*, 
and was carried out under the supervision of Professor [Tom Mens](https://staff.umons.ac.be/tom.mens/) and Doctor [Alexandre Decan](https://staff.umons.ac.be/alexandre.decan/indexEn.html).

More information concerning installation and terminology can be found in the [wiki](https://github.com/MrRose765/GitLab-Bot-identification/wiki).

## Abstract
Collaborative development platforms such as GitHub and GitLab play a central role in modern software projects, 
facilitating code management, collaboration between developers and automation of repetitive tasks. 
Automated agents (or bots) are widely used to automate these tasks, making it difficult to analyze contributor behavior. 
Several bot detection models have been proposed, including BIMBAS, a model based on the analysis of user activity sequences.
However, these models have been exclusively designed and evaluated on GitHub, which raises the question of 
their transferability to other platforms such as GitLab.

To enable BIMBAS to be applied to GitLab, we have adapted the ghmap tool, originally designed for GitHub to calculate user activity. 
Called “glmap”, this adaptation transforms the raw events exposed by the GitLab API into sequences of activities 
comparable to those generated on GitHub. Using this tool, we built up a dataset of 593 GitLab users, 
including both human and automated accounts. Evaluation of the BIMBAS model on this corpus, without modifying its architecture, 
achieved a weighted F1-score of over 93%, demonstrating the model's transferability to GitLab.

## Structure
This package is structured as follows:
- `gitbot_utils/`: Utility modules to fetch events from GitHub or GitLab and compute features.
- `notebooks/`: Jupyter notebooks for analysis and experiments.
- `resources/`: 
  - `data/`: Datasets (mainly feature sets) used to test and train the models.
  - `evals/`: Evaluation results and predictions of the models.
  - `models/`: Models used in this project. (Saved with joblib)
- `script/`: Python scripts maily used to generate the datasets.
  - `create_gitlab_dataset.py`: Contains functions used to extract bot and human contributors from GitLab repositories.
  - `extract_gitlab_repositories.py`: Used to extract the active repositories from GitLab.
  - `save_user_events.py`: Fetch the events from each user and save them in a file. (1 file per user)
  - `save_user_features.py`: Read the user events files and compute the features for each user. (Saves in csv)
