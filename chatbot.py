"""FAQ loading, validation and TF-IDF/cosine-similarity matching."""

import json
from pathlib import Path
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from preprocess import preprocess_text

DEFAULT_THRESHOLD = 0.30
FALLBACK_ANSWER = (
    "I'm sorry, I couldn't find a relevant answer to your question. "
    "Please try asking in a different way or choose one of the sample questions."
)


class FAQChatbot:
    """Retrieval-based FAQ chatbot using TF-IDF and cosine similarity."""

    def __init__(self, faq_path: str | Path, threshold: float = DEFAULT_THRESHOLD):
        self.faq_path = Path(faq_path)
        self.threshold = float(threshold)
        self.faqs: list[dict[str, str]] = []
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
        self.faq_matrix = None
        self.reload()

    @staticmethod
    def validate_faqs(data: Any) -> list[dict[str, str]]:
        if not isinstance(data, list):
            raise ValueError("FAQ dataset must contain a JSON array.")
        if not data:
            raise ValueError("FAQ dataset is empty.")

        validated = []
        for index, item in enumerate(data, start=1):
            if not isinstance(item, dict):
                raise ValueError(f"FAQ entry {index} must be an object.")
            question = item.get("question")
            answer = item.get("answer")
            if not isinstance(question, str) or not question.strip():
                raise ValueError(f"FAQ entry {index} has a missing/empty question.")
            if not isinstance(answer, str) or not answer.strip():
                raise ValueError(f"FAQ entry {index} has a missing/empty answer.")
            validated.append({"question": question.strip(), "answer": answer.strip()})
        return validated

    def load_faqs(self) -> list[dict[str, str]]:
        if not self.faq_path.exists():
            raise FileNotFoundError(f"FAQ file not found: {self.faq_path}")
        try:
            with self.faq_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid FAQ JSON: {exc.msg}") from exc
        return self.validate_faqs(data)

    def reload(self) -> None:
        """Reload the dataset and rebuild the TF-IDF model."""
        faqs = self.load_faqs()
        processed_questions = [preprocess_text(item["question"]) for item in faqs]
        if any(not question for question in processed_questions):
            raise ValueError("At least one FAQ question becomes empty after preprocessing.")

        self.faqs = faqs
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
        self.faq_matrix = self.vectorizer.fit_transform(processed_questions)

    def get_response(self, user_question: str) -> dict[str, Any]:
        """Return answer, confidence and matched FAQ for a user question."""
        if not isinstance(user_question, str):
            return {"answer": "Please enter your question as text.", "confidence": 0.0, "matched_question": None}

        user_question = user_question.strip()
        if not user_question:
            return {"answer": "Please enter a question so I can help you.", "confidence": 0.0, "matched_question": None}
        if len(user_question) > 500:
            return {"answer": "Please keep your question under 500 characters.", "confidence": 0.0, "matched_question": None}
        if len(user_question.split()) < 2:
            return {"answer": "Please provide a little more detail in your question.", "confidence": 0.0, "matched_question": None}

        processed = preprocess_text(user_question)
        if not processed:
            return {"answer": FALLBACK_ANSWER, "confidence": 0.0, "matched_question": None}

        query_vector = self.vectorizer.transform([processed])
        similarities = cosine_similarity(query_vector, self.faq_matrix)[0]
        best_index = int(similarities.argmax())
        best_score = float(similarities[best_index])
        matched = self.faqs[best_index]

        if best_score >= self.threshold:
            return {
                "answer": matched["answer"],
                "confidence": round(best_score, 4),
                "matched_question": matched["question"],
            }

        return {
            "answer": FALLBACK_ANSWER,
            "confidence": round(best_score, 4),
            "matched_question": None,
        }


def build_chatbot(faq_path: str | Path, threshold: float = DEFAULT_THRESHOLD) -> FAQChatbot:
    return FAQChatbot(faq_path, threshold)
