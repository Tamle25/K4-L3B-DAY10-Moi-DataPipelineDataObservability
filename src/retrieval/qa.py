from __future__ import annotations

from dataclasses import dataclass
import re

from core.config import Settings
from core.utils import first_sentence
from retrieval.index import LocalEmbeddingIndex, SearchResult


@dataclass(frozen=True)
class AnswerResult:
    question: str
    answer: str
    retrieved_doc_ids: list[str]
    retrieved_contexts: list[str]
    retrieved_titles: list[str]


def _extract_answer(question: str, top_result: SearchResult) -> str:
    lowered = question.lower()
    metadata = top_result.metadata
    if "author" in lowered:
        return metadata.get("authors_joined", "")
    if "when was" in lowered or "publication date" in lowered or "published" in lowered or "date" in lowered:
        return metadata.get("published", "")
    if "categor" in lowered:
        return metadata.get("categories_joined", "")
    return first_sentence(metadata.get("summary", ""))


def _generate_answer_with_llm(question: str, top_result: SearchResult, settings: Settings) -> str:
    try:
        from retrieval.llm import build_llm

        prompt = f"""You are a precise academic QA system. Based ONLY on the following paper context, answer the question concisely and directly.

Context:
{top_result.content}

Question: {question}

Instructions:
- If asking about authors, return the exact author names separated by comma.
- If asking about publication date, return only the date in YYYY-MM-DD format.
- If asking about categories, return the categories.
- If asking about summary, return the first key sentence of the summary.
- Do NOT add conversational filler or explanations. Answer directly.
""".strip()
        llm = build_llm(settings=settings, temperature=0.0)
        res = llm.invoke(prompt)
        content = res.content.strip() if hasattr(res, "content") else str(res).strip()
        # Clean any markdown quotation formatting if present
        content = re.sub(r"^[\"']|[\"']$", "", content).strip()
        return content or _extract_answer(question, top_result)
    except Exception:
        return _extract_answer(question, top_result)


def answer_question(question: str, settings: Settings, index: LocalEmbeddingIndex, top_k: int | None = None) -> AnswerResult:
    title_match = re.search(r"'([^']+)'", question)
    exact = index.lookup(title_match.group(1)) if title_match else None
    retrieved = index.search(question, top_k=top_k)
    if exact:
        exact_result = SearchResult(
            paper_id=exact["paper_id"],
            title=exact["title"],
            score=1.0,
            content=exact["content"],
            metadata=exact["metadata"],
        )
        deduped = [exact_result] + [item for item in retrieved if item.paper_id != exact_result.paper_id]
        retrieved = deduped[: (top_k or settings.top_k)]
    if not retrieved:
        answer = "I don't know from the indexed corpus."
    else:
        answer = _extract_answer(question, retrieved[0])
    return AnswerResult(
        question=question,
        answer=answer,
        retrieved_doc_ids=[item.paper_id for item in retrieved],
        retrieved_contexts=[item.content for item in retrieved],
        retrieved_titles=[item.title for item in retrieved],
    )
