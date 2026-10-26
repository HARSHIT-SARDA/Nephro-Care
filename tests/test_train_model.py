from pathlib import Path

from model_service import train_and_save_model, load_model_artifact


MODEL_PATH = Path("model/model.pkl")


def test_train_and_save_model():
    """
    Verify that the current NephroCare training pipeline
    can train the model and create the model artifact.
    """

    artifact = train_and_save_model()

    assert artifact is not None
    assert isinstance(artifact, dict)

    # Accuracy is returned by the current training pipeline.
    assert "accuracy" in artifact

    accuracy = artifact["accuracy"]

    assert 0 <= accuracy <= 1

    # Training should create the saved model artifact.
    assert MODEL_PATH.exists()


def test_load_model_artifact():
    """
    Verify that the saved model artifact can be loaded.
    """

    artifact = load_model_artifact()

    assert artifact is not None