import pytest

from chatbot import NO_MATCH_ANSWER, NOT_SURE_ANSWER, SMALL_TALK, FAQBot


@pytest.fixture(scope="module")
def bot():
    return FAQBot()


# Different wordings of FAQ questions (used while tuning the FAQ variants and thresholds).
PARAPHRASES = [
    ("how can i apply to ashwood", "How do I apply for admission?"),
    ("what's the fee for btech", "What is the fee for B.Tech?"),
    ("how much do I have to pay for engineering per year", "What is the fee for B.Tech?"),
    ("do you have hostels for girls", "Is hostel available?"),
    ("hostel charges per year", "What is the hostel fee?"),
    ("when is the deadline for applying", "What is the last date to apply?"),
    ("is JEE mandatory?", "Which entrance exams are accepted?"),
    ("can i get a scholarship", "Do you offer scholarships?"),
    ("what documents should i carry", "What documents do I need for admission?"),
    ("when does college start", "When do classes start?"),
    ("what is the average salary package", "How are the placements?"),
    ("can i pay fees in two parts", "Can I pay the fees in instalments?"),
    ("what's the address of the college", "Where is the college located?"),
    ("is there a bus service", "Is there a college bus?"),
    ("how do i get my money back if i cancel", "What is the refund policy if I cancel my admission?"),
    ("eligibility for mba", "What is the eligibility for MBA?"),
    ("list all courses", "What courses do you offer?"),
    ("how many years is bca", "How long is each course?"),
    ("is ragging there", "Is the campus safe? What about ragging?"),
    ("phone number of admission office", "How do I contact the admissions office?"),
    ("can i see the campus before joining", "Can I visit the campus?"),
    ("when will results come", "When will the merit list come out?"),
    ("is there wifi", "What facilities are on campus?"),
    ("can i edit my form", "Can I edit my application after submitting it?"),
    ("when do admissions open", "When do applications open?"),
    ("do you give internships", "Do you help with internships?"),
    ("what is the mba fee", "What is the fee for MBA?"),
    ("B.Tech eligibility", "What is the eligibility for B.Tech?"),
    ("minimum percentage for bca", "What is the eligibility for BCA?"),
    ("is there an entrance test for bba", "Which entrance exams are accepted?"),
]

# Questions never used for tuning, to measure how well matching generalises.
UNSEEN = [
    ("what is the procedure to take admission", "How do I apply for admission?"),
    ("do i need to pay to fill the form", "Is there an application fee?"),
    ("is the application fee refundable", "Is there an application fee?"),
    ("what are the btech fees", "What is the fee for B.Tech?"),
    ("how much is the bba fee", "What is the fee for BCA, BBA and B.Sc?"),
    ("is there a hostel for boys", "Is hostel available?"),
    ("how much is hostel and mess", "What is the hostel fee?"),
    ("what's the last date for mba applications", "What is the last date to apply?"),
    ("when do classes begin", "When do classes start?"),
    ("how many seats in computer science", "How many seats are there?"),
    ("can i switch branch", "Can I change my branch after the first year?"),
    ("where is the campus located", "Where is the college located?"),
    ("which documents are required", "What documents do I need for admission?"),
    ("what if my marksheet is not ready", "Can I submit some documents later?"),
    ("how good are placements", "How are the placements?"),
    ("how do i contact you", "How do I contact the admissions office?"),
    ("are evening classes available", "Do you offer part-time or distance courses?"),
    ("what is the duration of mca", "How long is each course?"),
    ("reservation for sc st students", "Is there reservation for SC, ST, OBC and EWS?"),
    ("what is the refund policy", "What is the refund policy if I cancel my admission?"),
    ("when is the gd pi for mba", "Is there an interview or group discussion?"),
    ("is there education loan facility", "Can I get an education loan?"),
]


def test_every_faq_matches_its_own_question(bot):
    for faq in bot.faqs:
        reply = bot.reply(faq["question"])
        assert reply.matched_question == faq["question"]
        assert reply.score == pytest.approx(1.0)


@pytest.mark.parametrize("message, expected", PARAPHRASES)
def test_paraphrases_match_the_right_faq(bot, message, expected):
    assert bot.reply(message).matched_question == expected


def test_accuracy_on_unseen_questions(bot):
    replies = [(bot.reply(message), expected) for message, expected in UNSEEN]
    answered = sum(reply.matched_question == expected for reply, expected in replies)
    answered_or_suggested = sum(expected in (reply.matched_question, *reply.suggestions) for reply, expected in replies)
    assert answered / len(UNSEEN) >= 0.85
    assert answered_or_suggested == len(UNSEEN)


@pytest.mark.parametrize("message", ["what's the weather in paris", "who won the cricket match", "recommend a good movie"])
def test_unrelated_questions_are_not_answered(bot, message):
    reply = bot.reply(message)
    assert reply.matched_question is None
    assert reply.answer == NO_MATCH_ANSWER
    assert reply.suggestions == bot.popular


def test_vague_question_gets_suggestions_instead_of_a_guess(bot):
    reply = bot.reply("fees")
    assert reply.matched_question is None
    assert reply.answer == NOT_SURE_ANSWER
    assert len(reply.suggestions) == 3
    assert all("fee" in question.lower() for question in reply.suggestions)


def test_small_talk(bot):
    assert bot.reply("hi!").matched_question == "Hello"
    assert bot.reply("thanks a lot").matched_question == "Thank you"
    assert bot.reply("what can you do?").matched_question == "Who are you?"
    assert bot.reply("thanks").suggestions == []


def test_followups_come_from_the_same_category(bot):
    reply = bot.reply("What is the hostel fee?")
    assert len(reply.suggestions) == 3
    assert reply.matched_question not in reply.suggestions
    categories = {faq["question"]: faq["category"] for faq in bot.faqs}
    assert {categories[question] for question in reply.suggestions} == {"Hostel & campus"}


def test_browse_categories_leave_out_small_talk(bot):
    categories = bot.categories()
    assert SMALL_TALK not in categories
    assert sum(len(questions) for questions in categories.values()) == 41
