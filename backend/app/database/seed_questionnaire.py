from __future__ import annotations

from sqlalchemy import select

from app.database.session import SessionLocal
from app.models.question import Question
from app.models.question_option import QuestionOption
from app.models.questionnaire import Questionnaire
from app.models.questionnaire_version import QuestionnaireVersion

QUESTIONNAIRE_NAME = "SDM Adapted Prakriti Questionnaire"
QUESTIONNAIRE_VERSION = 1

# Each tuple is (section, feature, vata characteristic, pitta characteristic,
# kapha characteristic). None means the source cell was blank or unavailable.
DOSHA_QUESTIONS = [
    ("Body Build and Skin", "Body size", "Thin and lean, low body weight", "Medium build, soft body", "Heavy, strong, well-built body"),
    ("Body Build and Skin", "Skin type", "Dry, rough, sometimes cracked", "Soft, warm, prone to moles, freckles, or pimples", "Oily, smooth, and glowing"),
    ("Body Build and Skin", "Joints", "Joints crack or make sound when moving", "Loose, soft joints and muscles", "Strong, firm, well-bound, and well-lubricated"),
    ("Body Build and Skin", "Body movement", "Fast, restless, always on the move (Having the habit of shaking Joints, eyes, eyebrows, jaw, lips, tongue, head, shoulders, hands and feet)", "Sharp and energetic", "Slow, steady, and calm"),
    ("Body Build and Skin", "Movement quality", "Light and quick in movement (also in eating and speech)", None, "Movements are heavy, firm, and grounded, supported by inner strength"),
    ("Hair, Nails, and Complexion", "Hair", "Thin, dry, and rough", "Turns grey early, may thin out or go bald early", "Thick, oily, wavy, and dark"),
    ("Hair, Nails, and Complexion", "Nails", "Dry and rough", None, "Smooth and glossy"),
    ("Hair, Nails, and Complexion", "Skin colour", "Dull, darker tone", "Yellowish or coppery tone", "Fair, cool-toned, glowing skin"),
    ("Hair, Nails, and Complexion", "Eyes", "Eyes move around a lot, unsteady gaze", "Eyes may look reddish inside", "Eyes are clear and calm-looking"),
    ("Appetite, Sweat, and Body Temperature", "Appetite", "Changes often, sometimes forgets to eat", "Very strong, feels hungry and eats a lot", "Low appetite, can skip meals easily"),
    ("Appetite, Sweat, and Body Temperature", "Thirst", "Variable", "Thirsty often", "Less thirsty"),
    ("Appetite, Sweat, and Body Temperature", "Sweating", None, "Sweats a lot, sweat may smell", "Sweats only a little"),
    ("Appetite, Sweat, and Body Temperature", "Weather preference", "Dislikes cold weather", "Dislikes hot weather", "Handles both hot and cold weather well"),
    ("Appetite, Sweat, and Body Temperature", "Elimination & body odour", "tendons and veins are prominently visible over the body", None, None),
    ("Voice and Way of Talking", "Voice quality", "Dry, hoarse, or cracking voice", "Sharp, clear, and convincing voice", "Deep, pleasant voice, smooth voice"),
    ("Voice and Way of Talking", "Talking style", "Talks a lot, talks fast", "Argues well, hard to out-talk in a debate", "Speaks slowly, thinks before speaking"),
    ("Voice and Way of Talking", "Speech and expression", "Talks a great deal", "Sharp or biting in speech", "Calm in talk"),
    ("Reproductive Health", "Reproductive strength", "Low reproductive vitality, desire is irregular and often weak", "Medium reproductive vitality, strong desire but tires quickly during intimacy", "High reproductive vitality, strong and steady desire, more likely to conceive"),
    ("Mind and Personality", "Thinking style", "Mind is restless, thoughts change quickly, good imagination but often unsure or confused", "Sharp, smart, and quick to understand things", "Calm, deep thinker, remembers things for a long time"),
    ("Mind and Personality", "Emotions", "Gets anxious or excited easily, mood changes fast", "Gets angry quickly, but also calms down quickly", "Stays calm, patient, and hard to upset"),
    ("Mind and Personality", "Behaviour with others", "May feel unlucky, can be envious or forgetful of favors done to them", "Does not bow down out of fear, but is kind to those who respect them", "Grateful, respectful, and loyal, especially in friendships"),
    ("Mind and Personality", "Starting new tasks", "Jumps into things quickly, but loses interest fast", "Starts with bold energy and confidence", "Slow to start, but steady once started"),
    ("Sleep", "Sleep pattern", "Light sleeper, wakes up easily, sleep is often disturbed", "Moderate sleep", "Deep, heavy sleeper, sleeps soundly"),
    ("Common Dreams", "What they usually dream of", "Flying in the sky, running, falling, or feeling out of control", "Fire, lightning, bright lights, or golden/shiny objects", "Lakes, ponds, lotus flowers, swans, and other calm water scenes"),
    ("Overall Strength in Life", "Physical strength", "Low", "Medium", "High"),
    ("Overall Strength in Life", "Lifespan", "Shorter", "Medium", "Longer"),
    ("Overall Strength in Life", "Ability to gain wealth", "Low, finds it hard to save money", "Medium", "High, tends to be prosperous"),
    ("Overall Strength in Life", "Knowledge and learning", "Unclear thinking, harder to stay focused", "Average understanding", "Learns well and remembers things for a long time"),
]

DIRGHAYU_SIGNS = [
    "Large hands, feet, flanks, nipple-tips, teeth, face, shoulders, forehead",
    "Long fingers, finger-joints, arms; deep/long breath; steady gaze",
    "Broad eyebrows, broad space between breasts, broad chest",
    "Short calves, short neck",
    "Deep/steady mind (courage), deep voice, deep-set umbilicus",
    "Ears and back of head well-grown, muscular, hairy",
    "After bathing, body dries from head downward first, heart region last",
    "Joints, veins and ligaments deep-set / not prominently visible (gūḍha)",
    "Compact, well-knit body (saṃhatāṅga)",
    "Steady sense organs (sthira-indriya)",
    "Each successive body region (feet → head) proportionately better formed than the one before",
    "Free from illness since birth; gradual, steady growth",
]


def _option(question: Question, text: str, dosha: str | None) -> QuestionOption:
    scores = {"vata": 0.0, "pitta": 0.0, "kapha": 0.0}
    if dosha is not None:
        scores[dosha] = 1.0
    return QuestionOption(
        question_id=question.id,
        option_text=text,
        vata_score=scores["vata"],
        pitta_score=scores["pitta"],
        kapha_score=scores["kapha"],
        sort_order=1,
    )


def seed_questionnaire() -> str:
    with SessionLocal() as db:
        questionnaire = db.scalar(
            select(Questionnaire).where(Questionnaire.name == QUESTIONNAIRE_NAME)
        )
        if questionnaire is None:
            questionnaire = Questionnaire(
                name=QUESTIONNAIRE_NAME,
                description=(
                    "SDM-provided questionnaire content for CCRAS PAS-based "
                    "scoring with an SDM-adapted questionnaire. HPL prototype; "
                    "not the official CCRAS AYUR Prakriti Portal."
                ),
                is_active=True,
            )
            db.add(questionnaire)
            db.flush()

        version = db.scalar(
            select(QuestionnaireVersion).where(
                QuestionnaireVersion.questionnaire_id == questionnaire.id,
                QuestionnaireVersion.version_number == QUESTIONNAIRE_VERSION,
            )
        )
        if version is None:
            version = QuestionnaireVersion(
                questionnaire_id=questionnaire.id,
                version_number=QUESTIONNAIRE_VERSION,
                title="SDM Adapted Prakriti Questionnaire v1",
                description="Questions with only explicitly populated SDM Dosha characteristics.",
            )
            db.add(version)
            db.flush()

        for sort_order, (section, feature, vata, pitta, kapha) in enumerate(
            DOSHA_QUESTIONS,
            start=1,
        ):
            question_text = f"{section}: {feature}"
            question = db.scalar(
                select(Question).where(
                    Question.questionnaire_version_id == version.id,
                    Question.question_text == question_text,
                )
            )
            if question is None and feature == "Elimination & body odour":
                question = db.scalar(
                    select(Question).where(
                        Question.questionnaire_version_id == version.id,
                        Question.question_text == f"{section}: Elimination and body odour",
                    )
                )
                if question is not None:
                    question.question_text = question_text
            if question is None:
                question = Question(
                    questionnaire_version_id=version.id,
                    question_text=question_text,
                    question_type="single_choice",
                    is_required=True,
                    sort_order=sort_order,
                )
                db.add(question)
                db.flush()
            for option_sort_order, (dosha, text) in enumerate(
                (("vata", vata), ("pitta", pitta), ("kapha", kapha)),
                start=1,
            ):
                if text and db.scalar(
                    select(QuestionOption.id).where(
                        QuestionOption.question_id == question.id,
                        QuestionOption.option_text == text,
                    )
                ) is None:
                    if (
                        feature == "Elimination & body odour"
                        and dosha == "vata"
                        and text == "tendons and veins are prominently visible over the body"
                    ):
                        legacy_option = db.scalar(
                            select(QuestionOption).where(
                                QuestionOption.question_id == question.id,
                                QuestionOption.option_text == "Tendons and veins are prominently visible over the body",
                            )
                        )
                        if legacy_option is not None:
                            legacy_option.option_text = text
                            continue
                    option = _option(question, text, dosha)
                    option.sort_order = option_sort_order
                    db.add(option)

        for index, sign in enumerate(DIRGHAYU_SIGNS, start=1):
            question_text = f"Dīrghāyu Lakṣaṇa {index}: {sign}"
            question = db.scalar(
                select(Question).where(
                    Question.questionnaire_version_id == version.id,
                    Question.question_text == question_text,
                )
            )
            if question is None:
                question = Question(
                    questionnaire_version_id=version.id,
                    question_text=question_text,
                    question_type="present_absent",
                    is_required=False,
                    sort_order=len(DOSHA_QUESTIONS) + index,
                )
                db.add(question)
                db.flush()
            for option_sort_order, option_text in ((1, "Present"), (2, "Absent")):
                if db.scalar(
                    select(QuestionOption.id).where(
                        QuestionOption.question_id == question.id,
                        QuestionOption.option_text == option_text,
                    )
                ) is None:
                    db.add(
                        QuestionOption(
                            question_id=question.id,
                            option_text=option_text,
                            sort_order=option_sort_order,
                        )
                    )

        lifespan_text = "Dīrghāyu Lakṣaṇa: Lifespan classification"
        lifespan = db.scalar(
            select(Question).where(
                Question.questionnaire_version_id == version.id,
                Question.question_text == lifespan_text,
            )
        )
        if lifespan is None:
            lifespan = Question(
                questionnaire_version_id=version.id,
                question_text=lifespan_text,
                question_type="single_choice",
                is_required=False,
                sort_order=len(DOSHA_QUESTIONS) + len(DIRGHAYU_SIGNS) + 1,
            )
            db.add(lifespan)
            db.flush()
        for option_sort_order, option_text in enumerate(
            ("Shorter", "Medium", "Longer"),
            start=1,
        ):
            if db.scalar(
                select(QuestionOption.id).where(
                    QuestionOption.question_id == lifespan.id,
                    QuestionOption.option_text == option_text,
                )
            ) is None:
                db.add(
                    QuestionOption(
                        question_id=lifespan.id,
                        option_text=option_text,
                        sort_order=option_sort_order,
                    )
                )

        db.commit()
        return questionnaire.id


if __name__ == "__main__":
    print(seed_questionnaire())
