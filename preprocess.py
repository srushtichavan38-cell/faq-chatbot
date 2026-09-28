"""NLP preprocessing utilities for the FAQ chatbot."""

import re
import string
from typing import List

import nltk

# Small fallback stopword set keeps the application usable even when the
# NLTK stopwords corpus has not been downloaded yet.
FALLBACK_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "how", "i", "in", "is", "it", "me", "of", "on", "or", "that", "the",
    "this", "to", "was", "what", "when", "where", "which", "who", "why",
    "with", "you", "your", "do", "does", "can", "could", "would", "should",
}


def _ensure_nltk_resources() -> None:
    """Check for NLTK resources without making startup depend on network access."""
    try:
        nltk.data.find("corpora/stopwords")
    except (LookupError, OSError):
        # Missing corpora are handled by the built-in fallback below.
        pass


def _get_stopwords() -> set[str]:
    _ensure_nltk_resources()
    try:
        from nltk.corpus import stopwords
        return set(stopwords.words("english"))
    except (LookupError, OSError):
        return FALLBACK_STOPWORDS


def _tokenize(text: str) -> List[str]:
    """Tokenize with NLTK when possible, otherwise use a safe regex fallback."""
    try:
        # word_tokenize can require punkt/punkt_tab depending on NLTK version.
        return nltk.word_tokenize(text)
    except (LookupError, OSError, ValueError):
        return re.findall(r"[A-Za-z0-9]+", text)


def preprocess_text(text: str) -> str:
    """Normalize text for FAQ matching.

    Steps: lowercase -> remove punctuation/special characters -> tokenize ->
    remove stopwords -> light stemming -> normalize whitespace.
    """
    if not isinstance(text, str):
        return ""

    text = text.lower().strip()
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = _tokenize(text)
    stop_words = _get_stopwords()

    filtered = [token for token in tokens if token.isalnum() and token not in stop_words]

    # Porter stemming is lightweight and available with the NLTK package.
    try:
        stemmer = nltk.stem.PorterStemmer()
        filtered = [stemmer.stem(token) for token in filtered]
    except Exception:
        pass

    return re.sub(r"\s+", " ", " ".join(filtered)).strip()
