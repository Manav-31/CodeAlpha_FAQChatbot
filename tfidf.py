"""TF-IDF vectors and cosine similarity, written out in plain Python.

Each document is a list of tokens. Its vector gives every term (single words
and adjacent word pairs) a weight:

    weight = (1 + log(count in document)) * idf
    idf    = log((1 + number of documents) / (1 + documents containing the term)) + 1

so words that appear in only a few documents count for more than common ones.
Vectors are scaled to length 1, which makes cosine similarity a plain dot product.
"""

import math
from collections import Counter


def terms(tokens):
    """Single words plus adjacent pairs, e.g. ["hostel", "fee"] -> ["hostel", "fee", "hostel fee"]."""
    return tokens + [f"{first} {second}" for first, second in zip(tokens, tokens[1:])]


class TfidfIndex:
    def __init__(self, documents):
        docs = [terms(tokens) for tokens in documents]
        doc_freq = Counter(term for doc in docs for term in set(doc))
        self.idf = {term: math.log((1 + len(docs)) / (1 + freq)) + 1 for term, freq in doc_freq.items()}
        self.vectors = [self._vector(doc) for doc in docs]

    def _vector(self, doc_terms):
        counts = Counter(term for term in doc_terms if term in self.idf)  # unseen words carry no weight
        vector = {term: (1 + math.log(count)) * self.idf[term] for term, count in counts.items()}
        length = math.sqrt(sum(weight * weight for weight in vector.values()))
        return {term: weight / length for term, weight in vector.items()} if length else {}

    def similarities(self, tokens):
        """Cosine similarity (0 to 1) between `tokens` and every indexed document."""
        query = self._vector(terms(tokens))
        return [sum(weight * doc.get(term, 0.0) for term, weight in query.items()) for doc in self.vectors]
