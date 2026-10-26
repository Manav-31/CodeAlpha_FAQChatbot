"""FAQ matching: TF-IDF vectors and cosine similarity over preprocessed questions."""

import json
from dataclasses import dataclass, field
from pathlib import Path

from nlp import ensure_nltk_data, preprocess
from tfidf import TfidfIndex

FAQ_FILE = Path(__file__).parent / "data" / "faqs.json"
MATCH_THRESHOLD = 0.45      # minimum similarity to answer directly
SMALL_TALK_THRESHOLD = 0.7  # small talk ("hi", "thanks") must be a near-exact match
SUGGEST_THRESHOLD = 0.1     # minimum similarity to offer a question as "did you mean"
SMALL_TALK = "Small talk"
NOT_SURE_ANSWER = "I'm not sure I understood that. Did you mean one of these?"
NO_MATCH_ANSWER = ("Sorry, I don't have an answer for that. Try asking about applying, courses, fees, "
                   "hostel or deadlines, or email admissions@ashwood.example.")


@dataclass
class Reply:
    answer: str
    matched_question: str | None = None
    category: str | None = None
    score: float = 0.0
    suggestions: list[str] = field(default_factory=list)


class FAQBot:
    def __init__(self, faq_file=FAQ_FILE):
        ensure_nltk_data()
        data = json.loads(Path(faq_file).read_text(encoding="utf-8"))
        self.college = data["college"]
        self.popular = data["popular"]
        self.faqs = data["faqs"]

        # Every phrasing of every question is one document; owners[i] is the FAQ it belongs to.
        documents, self.owners = [], []
        for index, faq in enumerate(self.faqs):
            for text in [faq["question"], *faq.get("variants", [])]:
                documents.append(preprocess(text))
                self.owners.append(index)
        self.index = TfidfIndex(documents)

    def categories(self):
        """FAQ questions grouped by category, for browsing. Small talk is left out."""
        grouped = {}
        for faq in self.faqs:
            if faq["category"] != SMALL_TALK:
                grouped.setdefault(faq["category"], []).append(faq["question"])
        return grouped

    def scores(self, message):
        """Cosine similarity between `message` and each FAQ, using the FAQ's closest phrasing."""
        best = [0.0] * len(self.faqs)
        for owner, similarity in zip(self.owners, self.index.similarities(preprocess(message))):
            best[owner] = max(best[owner], similarity)
        return best

    def reply(self, message):
        scores = self.scores(message)
        ranked = sorted(range(len(self.faqs)), key=lambda i: -scores[i])
        # Without this, "recommend a good movie" would get "Hi!" back because of "good morning".
        ranked = [i for i in ranked if self.faqs[i]["category"] != SMALL_TALK or scores[i] >= SMALL_TALK_THRESHOLD]
        top = ranked[0]
        top_score = round(scores[top], 2)

        if scores[top] >= MATCH_THRESHOLD:
            faq = self.faqs[top]
            return Reply(faq["answer"], faq["question"], faq["category"], top_score, self._followups(top, scores))

        close = [self.faqs[i]["question"] for i in ranked
                 if scores[i] >= SUGGEST_THRESHOLD and self.faqs[i]["category"] != SMALL_TALK][:3]
        if close:
            return Reply(NOT_SURE_ANSWER, score=top_score, suggestions=close)
        return Reply(NO_MATCH_ANSWER, score=top_score, suggestions=self.popular)

    def _followups(self, index, scores):
        """Questions to suggest after answering FAQ `index`."""
        faq = self.faqs[index]
        if "followups" in faq:
            return faq["followups"]
        if faq["category"] == SMALL_TALK:
            return []
        related = [i for i, other in enumerate(self.faqs) if i != index and other["category"] == faq["category"]]
        related.sort(key=lambda i: -scores[i])
        return [self.faqs[i]["question"] for i in related[:3]]
