# GitLab Bot Identification

## Installation
It is recommended to create a virtual environment to install the dependencies.
```bash
python3 -m venv venv
source venv/bin/activate
```

This project is divided into two parts:
1. **gitbot_utils**: This package contains the utils modules to fetch events from GitHub or GitLab, 
compute the activity mapping predict if a user is a bot or not.
2. Notebooks: Mainly contains analysis and experiments.

### Install gitbot_utils
```bash
pip install src/
```

### Install dependencies
```bash
cd src/notebooks
pip install -r requirements.txt
```

This requirements file contains the dependencies used only in the notebooks. (Maily for plotting)


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
- `BIMLAB`: `bimbas-ghmap-GitLab`

For example, `BIMBIS` is a model that has the architecture of **BIMBAS** but trained on the **new dataset** with the ghmap **activity mapping**.