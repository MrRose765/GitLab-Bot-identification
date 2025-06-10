# GitLab Bot Identification


This repository contains the source code and resources developed as part of my master's thesis in Computer Science 
at the [University of Mons](https://web.umons.ac.be/en/university/), conducted within the Software Engineering Lab of the Faculty of Science.

The thesis is entitled *"Study of the Transferability of the BIMBAS Bot Detection Model between GitHub and GitLab"*, 
and was carried out under the supervision of Professor [Tom Mens](https://staff.umons.ac.be/tom.mens/) and Doctor [Alexandre Decan](https://staff.umons.ac.be/alexandre.decan/indexEn.html).

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

More information concerning installation and terminology can be found in the [wiki](https://github.com/MrRose765/GitLab-Bot-identification/wiki).

## Installation
It is recommended to create a virtual environment to install the dependencies.
```bash
python3 -m venv venv
source venv/bin/activate
```

The dependencies of this project are divided into two parts:
1. **gitbot_utils**: This package contains utility modules to fetch events from GitHub or GitLab,
compute activity mappings, and predict whether a user is a bot or not.
2. Notebooks: Mainly contains analysis and experiments.

You can only install the dependencies `gitbot_utils` if you are not interested in the notebooks.
Be aware that installing only notebook dependencies will not be enough to run some of the notebooks.

### Install gitbot_utils
```bash
pip install src/
```

### Install dependencies for notebooks
```bash
cd src/notebooks
pip install -r requirements.txt
```

*Note*: The `requirements.txt` file contains the dependencies used only in the notebooks. (Mainly for plotting)


## Terminology
### Datasets
- `Old`: Dataset used in [RABBIT-Replication Package](https://github.com/natarajan-chidambaram/BIMBAS_RABBIT_replication_package)
- `New`: New dataset create for this project which consist of the contributors of the old dataset who
had at least 5 events on January 5, 2025.
- `GitLab`: Dataset from GitLab used in this project. (Not created yet)
### Activity Mapping
- `rbmap`: Activity mapping used in [RABBIT](https://github.com/natarajan-chidambaram/RABBIT)
- `ghmap`: Activity mapping developed in [ghmap](https://github.com/uhourri/ghmap)
- `glmap`: Activity mapping developed in this project for GitLab dataset. (based on [ghmap](https://github.com/uhourri/ghmap))

### Models
Each model is based on the bimbas architecture from [RABBIT](https://github.com/natarajan-chidambaram/RABBIT).  
To be clear, we will use the following convention to describe the models : `bimbas-M-D` where M is the mapping used and D is the training dataset.
Then, the models that are used in this project are:

- `BIMBAS`: `bimbas-rbmap-Old`  (Pretrained from [RABBIT](https://github.com/natarajan-chidambaram/RABBIT))
- `BIMBASELINE`: `bimbas-rbmap-New`
- `BIMBIS`: `bimbas-ghmap-New`
- `BIMLAB`: `bimbas-glmap-GitLab`

For example, `BIMBIS` is a model that has the architecture of **BIMBAS** but trained on the **new dataset** with the ghmap **activity mapping**.
