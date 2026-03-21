import pytest


@pytest.fixture(scope="session", autouse=True)
def spacy_init():
    """
    Initialize spaCy upfront, so that it does not run stray output into Jupyter Notebooks.
    """
    import spacy

    try:
        _nlp = spacy.load("en_core_web_sm")
    except OSError:
        raise OSError(
            "The spacy model 'en_core_web_sm' is required but not installed. "
            "Install it with: python -m spacy download en_core_web_sm"
        ) from None
