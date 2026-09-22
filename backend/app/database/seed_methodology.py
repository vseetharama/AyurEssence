from __future__ import annotations

import json

from sqlalchemy import select

from app.database.session import SessionLocal
from app.models.methodology import Methodology
from app.models.reference import Reference

METHODOLOGY_NAME = "CCRAS Standardized Prakriti Assessment Scale"
METHODOLOGY_VERSION = "1.0"

SCORING_CONFIGURATION = {
    "calculation_enabled": False,
    "total_predictors": 91,
    "vata_predictors": 31,
    "pitta_predictors": 29,
    "kapha_predictors": 32,
    "maximum_dosha_weight": 100 / 3,
    "weighted_score_formula": "(raw_score / predictor_count) * (100 / 3)",
    "question_option_mappings": {},
    "classification_rules": None,
    "limitations": [
        "The repository does not contain the approved CCRAS predictor-to-question mappings.",
        "The repository does not contain verified CCRAS Eka-Doshaja, Dwandaja/Sansargaja, or Sama-Doshaja classification rules.",
        "Calculation remains disabled until those source-controlled rules are supplied.",
    ],
}

REFERENCE_TITLE = "CCRAS Standardized Prakriti Assessment Scale methodology"
REFERENCE_CITATION = (
    "Aggregate methodology facts and formula supplied in the AyurEssence Phase 5 "
    "implementation brief; full publication metadata and question-level mappings "
    "are not present in this repository."
)


def seed_methodology() -> str:
    with SessionLocal() as db:
        methodology = db.scalar(
            select(Methodology).where(Methodology.name == METHODOLOGY_NAME)
        )
        if methodology is None:
            methodology = Methodology(
                name=METHODOLOGY_NAME,
                description=(
                    "Configuration record for the CCRAS Standardized Prakriti "
                    "Assessment Scale. This is a documented methodology reference, "
                    "not an official CCRAS portal or endorsement."
                ),
                version=METHODOLOGY_VERSION,
                scoring_rules=json.dumps(SCORING_CONFIGURATION, sort_keys=True),
            )
            db.add(methodology)
            db.flush()
        else:
            methodology.version = METHODOLOGY_VERSION
            methodology.scoring_rules = json.dumps(SCORING_CONFIGURATION, sort_keys=True)

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
                    author=None,
                    source="AyurEssence Phase 5 methodology brief",
                    citation=REFERENCE_CITATION,
                )
            )
        db.commit()
        return methodology.id


if __name__ == "__main__":
    print(seed_methodology())
