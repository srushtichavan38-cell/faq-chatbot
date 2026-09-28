import json
from pathlib import Path

import pytest

from chatbot import FALLBACK_ANSWER, FAQChatbot
from preprocess import preprocess_text

ROOT = Path(__file__).resolve().parents[1]
FAQ_PATH = ROOT / "data" / "faqs.json"


@pytest.fixture()
def bot():
    return FAQChatbot(FAQ_PATH, threshold=0.30)


def test_faq_dataset_loading(bot):
    assert len(bot.faqs) >= 40
    assert all(item["question"] and item["answer"] for item in bot.faqs)


def test_preprocessing():
    result = preprocess_text("  WHAT are the Admission Requirements?!  ")
    assert result
    assert result == result.lower()
    assert "?" not in result


def test_exact_question(bot):
    result = bot.get_response("How do I apply for admission?")
    assert result["matched_question"] == "How do I apply for admission?"
    assert result["confidence"] >= bot.threshold


def test_similar_question(bot):
    result = bot.get_response("How can I get admission to the college?")
    assert "admission" in result["answer"].lower() or "apply" in result["answer"].lower()
    assert result["matched_question"] is not None


def test_different_wording(bot):
    result = bot.get_response("What papers do I need to submit for admission")
    assert result["matched_question"] is not None


def test_case_punctuation_spaces(bot):
    result = bot.get_response("   WHAT ARE THE COLLEGE FEES???   ")
    assert result["matched_question"] is not None


def test_unknown_question(bot):
    result = bot.get_response("Tell me about the weather on Mars tomorrow")
    assert result["answer"] == FALLBACK_ANSWER
    assert result["matched_question"] is None
    assert result["confidence"] < bot.threshold


def test_empty_question(bot):
    result = bot.get_response("")
    assert result["matched_question"] is None
    assert result["confidence"] == 0.0


def test_short_question(bot):
    result = bot.get_response("fees")
    assert result["matched_question"] is None


def test_invalid_faq_structure(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps([{"question": "Only a question"}]), encoding="utf-8")
    with pytest.raises(ValueError):
        FAQChatbot(path)


def test_threshold_changes_behavior(bot):
    bot.threshold = 1.01
    result = bot.get_response("How do I apply for admission?")
    assert result["answer"] == FALLBACK_ANSWER
    assert result["matched_question"] is None
