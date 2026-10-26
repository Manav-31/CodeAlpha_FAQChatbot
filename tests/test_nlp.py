from nlp import ensure_nltk_data, preprocess

ensure_nltk_data()


def test_lowercases_and_drops_punctuation_and_stopwords():
    assert preprocess("What is the FEE?!") == ["fee"]


def test_stems_word_forms_to_the_same_root():
    assert preprocess("Applying for courses") == ["appli", "cours"]
    assert preprocess("applied") == preprocess("apply") == preprocess("application") == ["appli"]


def test_degree_names_are_normalised():
    assert preprocess("B.Tech") == preprocess("b. tech") == preprocess("btech") == ["btech"]


def test_wifi_spellings_are_normalised():
    assert preprocess("Wi-Fi") == preprocess("wi fi") == preprocess("wifi") == ["wifi"]


def test_synonyms_map_to_the_same_word():
    assert preprocess("accommodation price") == preprocess("hostel cost") == ["hostel", "fee"]


def test_filler_words_are_dropped():
    assert preprocess("Please tell me the college fee") == ["fee"]


def test_question_made_only_of_stopwords_is_kept():
    assert preprocess("Who are you?") == ["who", "are", "you"]


def test_empty_and_punctuation_only_input():
    assert preprocess("") == []
    assert preprocess("?!...") == []
