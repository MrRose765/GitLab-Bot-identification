# Rabbit Offline
This package includes a modified version of [rabbit](https://github.com/natarajan-chidambaram/RABBIT) to make it work in a local environment. This modified version was created in order to help a PhD student from the Software Engineering lab of the University of Mons (UMons).

The purpose of this version is to enable bot detection using a list of user events retrieved (previously) from the GitLab API. Given these events, the tool predicts whether the users involved are bots or not. This functionality is particularly useful for filtering out bot accounts from datasets, allowing for a more accurate analysis of human activity within software repositories.

An archive containing Rabbit Offline and a basic example is available is this release, or can be downloaded [here](https://github.com/user-attachments/files/19762281/rabbit_offline.zip).

## How to use

It is recommended to use a virtual environment to avoid any conflict with other packages installed on your machine.

To install the required dependencies, you can run the following command in the folder:
```bash
pip install -r requirements.txt
```

Once the environment is set up, you can modify the main function in `RabbitOffline.py` to use it. The following example demonstrates how to execute the detection on a json file that contains the events of a GitHub user.
```python
csv_file = 'events.json'

with open(csv_file, 'r') as file:
    events = json.load(file)

contributor_type, conf = predict_user(events)
print(f"Contributor type: {contributor_type}, Confidence: {conf}")
```
