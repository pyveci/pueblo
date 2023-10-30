from pueblo.nlp.resource import CachedWebResource


def test_cached_web_resource():
    url = "https://github.com/langchain-ai/langchain/raw/v0.0.325/docs/docs/modules/state_of_the_union.txt"
    docs = CachedWebResource(url).langchain_documents(chunk_size=1000, chunk_overlap=0)
    assert len(docs) == 42

    from langchain.schema import Document

    assert isinstance(docs[0], Document)
