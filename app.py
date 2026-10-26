"""Ashwood admissions FAQ chatbot - Flask web app.

Run:  python app.py   then open http://127.0.0.1:5000
"""

import os
from dataclasses import asdict

from flask import Flask, jsonify, render_template, request

from chatbot import FAQBot

MAX_MESSAGE_CHARS = 300

app = Flask(__name__)
# Jinja's tojson sorts keys by default; keep FAQ topics in the order they appear in faqs.json.
app.jinja_env.policies["json.dumps_kwargs"] = {"sort_keys": False}
bot = FAQBot()


@app.get("/")
def index():
    return render_template("index.html", college=bot.college, popular=bot.popular, categories=bot.categories())


@app.post("/api/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    message = str(payload.get("message") or "").strip()
    # Questions already answered in this chat, so they aren't suggested again.
    asked = payload.get("asked")
    asked = [question for question in asked if isinstance(question, str)] if isinstance(asked, list) else []

    if not message:
        return jsonify(error="Please type a question."), 400
    if len(message) > MAX_MESSAGE_CHARS:
        return jsonify(error=f"Please keep your question under {MAX_MESSAGE_CHARS} characters."), 400

    return jsonify(asdict(bot.reply(message, exclude=asked)))


if __name__ == "__main__":
    app.run(port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG") == "1")
