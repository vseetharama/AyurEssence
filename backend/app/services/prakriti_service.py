from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.models.assessment_response import AssessmentResponse
from app.models.dosha_result import DoshaResult
from app.models.methodology import Methodology
from app.models.question import Question
from app.models.question_option import QuestionOption


class CalculationValidationError(Exception):
    def __init__(self, detail: str, status_code: int = 400) -> None:
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


@dataclass(frozen=True)
class CalculatedScores:
    vata_percentage: float
    pitta_percentage: float
    kapha_percentage: float
    dominant_dosha: str | None


def _load_configuration(methodology: Methodology) -> dict[str, Any]:
    if not methodology.scoring_rules:
        raise CalculationValidationError("Methodology scoring configuration is missing.", 409)
    try:
        configuration = json.loads(methodology.scoring_rules)
    except json.JSONDecodeError:
        raise CalculationValidationError("Methodology scoring configuration is invalid.", 409) from None
    if not isinstance(configuration, dict):
        raise CalculationValidationError("Methodology scoring configuration is invalid.", 409)
    return configuration


def _validate_configuration(configuration: dict[str, Any]) -> None:
    if configuration.get("calculation_enabled") is not True:
        raise CalculationValidationError(
            "Methodology calculation is disabled until approved scoring data is configured.",
            409,
        )
    required = ("vata_predictors", "pitta_predictors", "kapha_predictors")
    if any(not isinstance(configuration.get(key), (int, float)) or configuration[key] <= 0 for key in required):
        raise CalculationValidationError("Methodology predictor counts are invalid.", 409)
    mappings = configuration.get("question_option_mappings")
    if not isinstance(mappings, dict) or not mappings:
        raise CalculationValidationError(
            "Question-level methodology scoring mappings are unavailable; calculation is disabled.",
            409,
        )
    if not isinstance(configuration.get("classification_rules"), dict):
        raise CalculationValidationError(
            "Verified methodology classification rules are unavailable; calculation is disabled.",
            409,
        )


def _classify(scores: dict[str, float], rules: dict[str, Any]) -> str:
    if rules.get("strategy") != "highest_weighted_score":
        raise CalculationValidationError("Methodology classification strategy is unsupported.", 409)
    highest = max(scores.values())
    winners = [name for name, value in scores.items() if value == highest]
    return "+".join(winners) if len(winners) > 1 else winners[0]


def calculate_scores(
    db: Session,
    assessment: Assessment,
    methodology: Methodology,
) -> CalculatedScores:
    configuration = _load_configuration(methodology)
    _validate_configuration(configuration)
    responses = list(
        db.scalars(
            select(AssessmentResponse)
            .where(AssessmentResponse.assessment_id == assessment.id)
        ).all()
    )
    questions = list(
        db.scalars(
            select(Question).where(
                Question.questionnaire_version_id == assessment.questionnaire_version_id
            )
        ).all()
    )
    required_ids = {question.id for question in questions if question.is_required}
    response_by_question = {response.question_id: response for response in responses}
    if not required_ids.issubset(response_by_question):
        raise CalculationValidationError("Required questionnaire responses are missing.")
    question_ids = {question.id for question in questions}
    for response in responses:
        if response.question_id not in question_ids:
            raise CalculationValidationError(
                "Assessment contains a response from another questionnaire version.",
                409,
            )
        if response.option_id is None:
            raise CalculationValidationError("Assessment response is missing an option.")
        option = db.get(QuestionOption, response.option_id)
        if option is None or option.question_id != response.question_id:
            raise CalculationValidationError(
                "Assessment response contains an invalid question/option relationship.",
                409,
            )

    raw = {"vata": 0.0, "pitta": 0.0, "kapha": 0.0}
    mappings = configuration["question_option_mappings"]
    for response in responses:
        mapping = mappings.get(response.option_id or "")
        if not isinstance(mapping, dict) or any(key not in mapping for key in raw):
            raise CalculationValidationError(
                "Methodology scoring mapping is missing for a submitted option.",
                409,
            )
        for dosha in raw:
            if not isinstance(mapping[dosha], (int, float)):
                raise CalculationValidationError("Methodology scoring mapping is invalid.", 409)
            raw[dosha] += float(mapping[dosha])

    counts = {
        "vata": float(configuration["vata_predictors"]),
        "pitta": float(configuration["pitta_predictors"]),
        "kapha": float(configuration["kapha_predictors"]),
    }
    percentages = {
        dosha: (raw[dosha] / counts[dosha]) * (100 / 3)
        for dosha in raw
    }
    dominant = _classify(percentages, configuration["classification_rules"])
    return CalculatedScores(
        vata_percentage=percentages["vata"],
        pitta_percentage=percentages["pitta"],
        kapha_percentage=percentages["kapha"],
        dominant_dosha=dominant,
    )


def calculate_and_persist(
    db: Session,
    assessment: Assessment,
    methodology: Methodology,
) -> DoshaResult:
    scores = calculate_scores(db, assessment, methodology)
    result = db.scalar(select(DoshaResult).where(DoshaResult.assessment_id == assessment.id))
    if result is None:
        result = DoshaResult(assessment_id=assessment.id)
        db.add(result)
    result.methodology_id = methodology.id
    result.vata_percentage = scores.vata_percentage
    result.pitta_percentage = scores.pitta_percentage
    result.kapha_percentage = scores.kapha_percentage
    result.dominant_dosha = scores.dominant_dosha
    result.notes = "Calculated from configured methodology mappings; observations are contextual only."
    db.commit()
    db.refresh(result)
    return result
