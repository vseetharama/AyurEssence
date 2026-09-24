from __future__ import annotations

import json

from sqlalchemy import select

from app.database.seed_questionnaire import QUESTIONNAIRE_NAME, seed_questionnaire
from app.database.session import SessionLocal
from app.models.methodology import Methodology
from app.models.question import Question
from app.models.question_option import QuestionOption
from app.models.questionnaire import Questionnaire
from app.models.questionnaire_version import QuestionnaireVersion
from app.models.reference import Reference

METHODOLOGY_NAME = "CCRAS PAS-Based Scoring - SDM Adapted Questionnaire"
METHODOLOGY_VERSION = "1.0"
METHODOLOGY_DESCRIPTION = (
    "Configuration record for the CCRAS Standardized Prakriti Assessment Scale "
    "used as the methodological basis for an SDM-adapted questionnaire. This is "
    "an HPL prototype, not the official CCRAS AYUR Prakriti Portal, and does not "
    "claim CCRAS endorsement."
)

REFERENCE_TITLE = "CCRAS PAS methodology for an SDM-adapted questionnaire"
REFERENCE_CITATION = (
    "Central Council for Research in Ayurvedic Sciences (CCRAS), Ministry of AYUSH, "
    "Standardized Prakriti Assessment Scale. Exact publication/manual metadata and "
    "official URL require confirmation from the approved source."
)


def _build_scoring_configuration(db) -> dict[str, object]:
    questionnaire = db.scalar(
        select(Questionnaire).where(Questionnaire.name == QUESTIONNAIRE_NAME)
    )
    if questionnaire is None:
        raise RuntimeError("SDM questionnaire must be seeded before methodology configuration.")
    version = db.scalar(
        select(QuestionnaireVersion).where(
            QuestionnaireVersion.questionnaire_id == questionnaire.id,
            QuestionnaireVersion.version_number == 1,
        )
    )
    if version is None:
        raise RuntimeError("SDM questionnaire version is missing.")

    questions = list(
        db.scalars(
            select(Question).where(Question.questionnaire_version_id == version.id)
        ).all()
    )
    options = list(
        db.scalars(
            select(QuestionOption).where(
                QuestionOption.question_id.in_([question.id for question in questions])
            )
        ).all()
    )
    mappings = {}
    scoring_question_ids = []
    predictor_counts = {"vata": 0, "pitta": 0, "kapha": 0}
    options_by_question: dict[str, list[QuestionOption]] = {}
    for option in options:
        options_by_question.setdefault(option.question_id, []).append(option)
        mapping = {
            "vata": option.vata_score,
            "pitta": option.pitta_score,
            "kapha": option.kapha_score,
        }
        if any(mapping.values()):
            mappings[option.id] = mapping

    for question in questions:
        question_options = options_by_question.get(question.id, [])
        doshas = {
            dosha
            for option in question_options
            for dosha, score in {
                "vata": option.vata_score,
                "pitta": option.pitta_score,
                "kapha": option.kapha_score,
            }.items()
            if score == 1
        }
        if doshas:
            scoring_question_ids.append(question.id)
            for dosha in doshas:
                predictor_counts[dosha] += 1

    return {
        "calculation_enabled": False,
        "methodology_basis": "CCRAS Standardized Prakriti Assessment Scale",
        "questionnaire_source": "SDM-provided Prakriti Question Bank",
        "adaptation": True,
        "scoring_unit": "one_mark_per_matching_predictor",
        "total_predictors": sum(predictor_counts.values()),
        "vata_predictors": predictor_counts["vata"],
        "pitta_predictors": predictor_counts["pitta"],
        "kapha_predictors": predictor_counts["kapha"],
        "weighting_formula": "(raw_score / predictor_count) * (100 / 3)",
        "scoring_question_ids": scoring_question_ids,
        "question_option_mappings": mappings,
        "classification_rules": {
            "method": "ccras_pas_based",
            "samadoshaja": {
                "minimum_percentage": 30,
                "maximum_percentage": 34,
                "inclusive": True,
            },
            "ekadoshaja": {
                "dominant_percentage_greater_than": 50,
                "margin_over_second_greater_than": 25,
            },
            "dwandaja": {
                "dominant_first": True,
                "equal_percentage_tie_breaker": "raw_score",
            },
            "classification_source_status": "published boundary table requires verification",
        },
        "dirghayu": {
            "separate_from_dosha_scoring": True,
            "visible_sign_count": 12,
            "document_threshold_present": 8,
            "document_item_range_discrepancy": "document says items 1-13 but 12 signs are visible",
        },
        "limitations": [
            "Calculation remains disabled until the complete approved classification table is verified.",
            "Dīrghāyu is stored as separate questionnaire responses and is not a Dosha predictor.",
        ],
    }


def seed_methodology() -> str:
    seed_questionnaire()
    with SessionLocal() as db:
        scoring_configuration = _build_scoring_configuration(db)
        methodology = db.scalar(
            select(Methodology).where(Methodology.name == METHODOLOGY_NAME)
        )
        if methodology is None:
            methodology = Methodology(
                name=METHODOLOGY_NAME,
                description=METHODOLOGY_DESCRIPTION,
                version=METHODOLOGY_VERSION,
                scoring_rules=json.dumps(scoring_configuration, sort_keys=True),
            )
            db.add(methodology)
            db.flush()
        else:
            methodology.description = METHODOLOGY_DESCRIPTION
            methodology.version = METHODOLOGY_VERSION
            methodology.scoring_rules = json.dumps(scoring_configuration, sort_keys=True)

        reference = db.scalar(
            select(Reference).where(
                Reference.methodology_id == methodology.id,
                Reference.title == REFERENCE_TITLE,
            )
        )
        if reference is None:
            db.add(
                Reference(
                    methodology_id=methodology.id,
                    title=REFERENCE_TITLE,
                    author="Central Council for Research in Ayurvedic Sciences (CCRAS)",
                    source="CCRAS / Ministry of AYUSH",
                    citation=REFERENCE_CITATION,
                )
            )
        db.commit()
        return methodology.id


if __name__ == "__main__":
    print(seed_methodology())
