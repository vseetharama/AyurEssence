from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.questionnaire import Questionnaire
from app.models.questionnaire_version import QuestionnaireVersion
from app.models.question import Question


def get_questionnaire(db: Session, questionnaire_id: str) -> Questionnaire | None:
    statement = (
        select(Questionnaire)
        .where(Questionnaire.id == questionnaire_id)
        .options(
            selectinload(Questionnaire.versions)
            .selectinload(QuestionnaireVersion.questions)
            .selectinload(Question.options)
        )
    )
    return db.scalar(statement)


def questionnaire_response(questionnaire: Questionnaire) -> dict[str, object]:
    versions = []
    for version in sorted(questionnaire.versions, key=lambda item: item.version_number):
        questions = []
        for question in sorted(version.questions, key=lambda item: item.sort_order):
            questions.append(
                {
                    "id": question.id,
                    "question_text": question.question_text,
                    "question_type": question.question_type,
                    "is_required": question.is_required,
                    "question_order": question.sort_order,
                    "options": [
                        {
                            "id": option.id,
                            "option_text": option.option_text,
                        }
                        for option in sorted(question.options, key=lambda item: item.sort_order)
                    ],
                }
            )
        versions.append(
            {
                "id": version.id,
                "version_number": version.version_number,
                "title": version.title,
                "description": version.description,
                "questions": questions,
            }
        )
    return {
        "id": questionnaire.id,
        "name": questionnaire.name,
        "description": questionnaire.description,
        "is_active": questionnaire.is_active,
        "versions": versions,
    }
