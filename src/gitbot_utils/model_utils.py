import warnings

import joblib
import rabbit as rb


def predict_contributor(features, model):
    """
    Predict if a contributor is a bot or not with a given model (BIMBAS architecture).

    Parameters:
        features: A DataFrame with the features of the contributor.
        model: The model to use to predict the type of contributor.

    Returns:
        contributor_type (str) - type of contributor determined based on probability ('Bot' or 'Human')
        confidence (float) - confidence score of the determined type (value between 0.0 and 1.0)
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        proba = model.predict_proba(features)
    return rb.compute_confidence(proba[0][1])


def load_model(model_path=None):
    """
    Load a .joblib model from a given path. If no path is provided, the default model from RABBIT is loaded.

    Parameters:
        model_path (str) - path to the model to load (default: None)

    Returns:
        model - loaded model
    """
    if not model_path:
        return rb.get_model()
    return joblib.load(model_path)
