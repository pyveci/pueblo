import pytest


@pytest.fixture(scope="session", autouse=True)
def nltk_init():
    """
    Initialize nltk upfront, so that it does not run stray output into Jupyter Notebooks.
    """
    download_items = ["averaged_perceptron_tagger", "punkt"]
    import nltk

    for item in download_items:
        nltk.download(item)
