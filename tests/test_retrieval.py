"""Kiem thu module Retrieval & QA Agent."""
from core.config import Settings
from core.utils import read_json
from retrieval.index import LocalEmbeddingIndex
from retrieval.qa import answer_question


def test_index_initialization_and_lookup(settings: Settings):
    assert settings.paths.embeddings_json.exists(), "Embeddings json phải tồn tại"
    index = LocalEmbeddingIndex.load(settings, settings.paths.embeddings_json)

    manifest = read_json(settings.paths.embeddings_json)
    first_title = manifest["documents"][0]["title"]
    exact = index.lookup(first_title)
    assert exact is not None
    assert exact["title"].lower() == first_title.lower()


def test_search_similarity(settings: Settings):
    index = LocalEmbeddingIndex.load(settings, settings.paths.embeddings_json)
    results = index.search("Data Observability and Quality Gates", top_k=3)
    assert len(results) > 0
    assert results[0].score >= 0.0
    assert "Title:" in results[0].content


def test_qa_answer_extraction(settings: Settings):
    index = LocalEmbeddingIndex.load(settings, settings.paths.embeddings_json)
    manifest = read_json(settings.paths.embeddings_json)
    first_doc = manifest["documents"][0]

    # 1. Author question
    q_author = f"Who are the authors of the paper '{first_doc['title']}'?"
    res_author = answer_question(q_author, settings=settings, index=index)
    assert len(res_author.answer) > 0
    assert res_author.answer == first_doc["metadata"]["authors_joined"]

    # 2. Date question
    q_date = f"When was the paper '{first_doc['title']}' published?"
    res_date = answer_question(q_date, settings=settings, index=index)
    assert res_date.answer == first_doc["metadata"]["published"]
