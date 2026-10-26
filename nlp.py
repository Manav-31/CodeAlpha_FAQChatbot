"""Text preprocessing with NLTK: tokenize, clean, remove stopwords, stem."""

import re
from functools import cache

import nltk
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer
from nltk.tokenize import word_tokenize

# Joins degree names so "B.Tech", "b. tech" and "b tech" all become "btech".
DEGREE_PATTERN = re.compile(r"\b([bm])\.?\s?(tech|sc|com|ca|ba)\b")
WIFI_PATTERN = re.compile(r"\bwi[\s-]?fi\b")

# Words people use interchangeably, mapped to the word the FAQs use.
SYNONYMS = {
    "cost": "fee", "price": "fee", "charge": "fee", "expense": "fee",
    "accommodation": "hostel", "dorm": "hostel", "dormitory": "hostel",
    "engineering": "btech",
    "programme": "course", "program": "course", "degree": "course",
    "application": "apply", "admit": "admission",
    "installment": "instalment", "emi": "instalment",
    "transport": "bus", "transportation": "bus",
    "concession": "scholarship", "waiver": "scholarship", "aid": "scholarship",
    "phone": "contact", "call": "contact", "email": "contact", "mail": "contact",
    "tour": "visit",
    "address": "location", "situated": "location",
    "eligible": "eligibility", "criteria": "eligibility", "qualification": "eligibility",
    "job": "placement", "recruitment": "placement", "recruit": "placement", "salary": "placement",
    "certificate": "document",
    "begin": "start", "commence": "start",
    "withdraw": "cancel",
    "safe": "safety", "security": "safety",
}

# Filler words common in questions that say nothing about the topic. "college" and
# "ashwood" are in every question someone could ask this bot, so they don't help either.
EXTRA_STOPWORDS = {"please", "kindly", "tell", "know", "want", "like", "would", "could",
                   "get", "give", "need", "help", "also", "college", "ashwood"}

_stemmer = SnowballStemmer("english")
# Synonyms are looked up after stemming, so stem both sides once up front.
_STEMMED_SYNONYMS = {_stemmer.stem(word): _stemmer.stem(target) for word, target in SYNONYMS.items()}


def ensure_nltk_data():
    """Download the NLTK data this module needs, if it isn't installed yet."""
    checks = {
        "punkt_tab": lambda: word_tokenize("check"),
        "stopwords": lambda: stopwords.words("english"),
    }
    for package, check in checks.items():
        try:
            check()
        except LookupError:
            nltk.download(package, quiet=True)


@cache
def _stopwords():
    return frozenset(stopwords.words("english")) | EXTRA_STOPWORDS


def preprocess(text):
    """Turn raw text into a list of normalised tokens ready for TF-IDF."""
    text = DEGREE_PATTERN.sub(r"\1\2", text.lower())
    text = WIFI_PATTERN.sub("wifi", text).replace("-", " ")
    tokens = [token for token in word_tokenize(text) if token.isalnum()]  # drops punctuation
    content = [token for token in tokens if token not in _stopwords()]
    # A question made only of stopwords ("who are you?") keeps them, so it can still be matched.
    stems = (_stemmer.stem(token) for token in content or tokens)
    return [_STEMMED_SYNONYMS.get(stem, stem) for stem in stems]
