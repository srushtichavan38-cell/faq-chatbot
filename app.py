"""Flask web application for the FAQ chatbot."""

import logging
import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from chatbot import FALLBACK_ANSWER, build_chatbot

BASE_DIR = Path(__file__).resolve().parent
FAQ_PATH = BASE_DIR / "data" / "faqs.json"
THRESHOLD = float(os.getenv("FAQ_THRESHOLD", "0.30"))
MAX_MESSAGE_LENGTH = 500

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024  # Basic request-size protection.

try:
    chatbot = build_chatbot(FAQ_PATH, THRESHOLD)
    startup_error = None
except Exception as exc:
    chatbot = None
    startup_error = str(exc)
    logger.exception("Could not initialize FAQ chatbot")


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/chat")
def chat():
    if chatbot is None:
        return jsonify({"error": "The chatbot is not initialized. Please check the FAQ dataset."}), 500

    if not request.is_json:
        return jsonify({"error": "Request must use application/json."}), 400

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Invalid JSON request body."}), 400

    message = payload.get("message")
    if not isinstance(message, str):
        return jsonify({"error": "The 'message' field must be a string."}), 400

    message = message.strip()
    if not message:
        return jsonify({"error": "Please enter a question."}), 400
    if len(message) > MAX_MESSAGE_LENGTH:
        return jsonify({"error": f"Please keep your question under {MAX_MESSAGE_LENGTH} characters."}), 400

    try:
        result = chatbot.get_response(message)
        return jsonify(result)
    except Exception:
        logger.exception("Error while processing chat request")
        return jsonify({"error": "Sorry, something went wrong while processing your question."}), 500


@app.get("/health")
def health():
    return jsonify({
        "status": "ok" if chatbot is not None else "error",
        "faq_count": len(chatbot.faqs) if chatbot else 0,
        "threshold": THRESHOLD,
        "startup_error": startup_error,
    })


@app.errorhandler(413)
def request_too_large(_error):
    return jsonify({"error": "Request is too large."}), 413


@app.errorhandler(404)
def not_found(_error):
    return jsonify({"error": "Endpoint not found."}), 404


@app.errorhandler(500)
def internal_error(_error):
    return jsonify({"error": "Internal server error."}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=False)
