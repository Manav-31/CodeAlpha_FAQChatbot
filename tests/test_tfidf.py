import pytest

from tfidf import TfidfIndex, terms


def test_terms_include_adjacent_word_pairs():
    assert terms(["hostel", "fee", "year"]) == ["hostel", "fee", "year", "hostel fee", "fee year"]


def test_identical_document_scores_one_and_unrelated_scores_zero():
    index = TfidfIndex([["hostel", "fee"], ["merit", "list"]])
    assert index.similarities(["hostel", "fee"]) == pytest.approx([1.0, 0.0])


def test_rare_words_count_for_more_than_common_ones():
    # "fee" is in every document, "btech" in only one.
    index = TfidfIndex([["fee", "btech"], ["fee", "hostel"], ["fee", "mba"]])
    btech_doc = 0
    assert index.similarities(["btech"])[btech_doc] > index.similarities(["fee"])[btech_doc]


def test_unseen_words_are_ignored():
    index = TfidfIndex([["hostel", "fee"]])
    assert index.similarities(["pizza"]) == [0.0]
    assert index.similarities(["pizza", "hostel"]) == index.similarities(["hostel"])
