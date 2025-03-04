# GitLab Bot Identification



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
- `BIMBAS`: pre-trained model from [RABBIT](https://github.com/natarajan-chidambaram/RABBIT)
- `BIMBASELINE`: BIMBAS architecture but trained on the new dataset with rbmap.
- `BIMBIS`: BIMBAS architecture but trained on the new dataset with ghmap.
- `BIMLAB`: BIMBAS architecture but trained on GitLab dataset with ghmap activity mapping.
### Evaluations
For the evaluations, we will use a convention. The convention is like `MODEL-DATASET-MAPPING`.  
For example, `BIMBASELINE-New-rbmap` means the BIMBASELINE model tested on the new dataset with rbmap.

