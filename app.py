"""Ashwood admissions FAQ chatbot - Flask web app.

Run:  python app.py   then open http://127.0.0.1:5000
"""

import os
from dataclasses import asdict

from flask import Flask, jsonify, render_template, request

from chatbot import FAQBot

MAX_MESSAGE_CHARS = 300

app = Flask(__name__)
bot = FAQBot()


@app.get("/")
def index():
    return render_template("index.html", college=bot.college, popular=bot.popular, categories=bot.categories())


@app.post("/api/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    message = str(payload.get("message") or "").strip()

    if not message:
        return jsonify(error="Please type a question."), 400
    if len(message) > MAX_MESSAGE_CHARS:
        return jsonify(error=f"Please keep your question under {MAX_MESSAGE_CHARS} characters."), 400

    return jsonify(asdict(bot.reply(message)))


if __name__ == "__main__":
    app.run(port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG") == "1")
