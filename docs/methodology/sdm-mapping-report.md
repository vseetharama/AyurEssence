# SDM Questionnaire Mapping Report

## Scope

AyurEssence uses CCRAS PAS-based scoring with an SDM-adapted questionnaire. The questionnaire content is sourced from `prakriti-question-bank.docx`; this is not the complete official CCRAS PAS questionnaire.

## Dosha predictor counts

The SDM document contains 28 logical Dosha feature questions. Counting only explicitly populated Vata, Pitta, and Kapha cells gives:

- Vata: 27 mapped predictors
- Pitta: 25 mapped predictors
- Kapha: 27 mapped predictors

These counts are for the SDM adaptation and must not be replaced with the complete CCRAS PAS counts of 31, 29, and 32.

## Sections

1. Body Build and Skin
2. Hair, Nails, and Complexion
3. Appetite, Sweat, and Body Temperature
4. Voice and Way of Talking
5. Reproductive Health
6. Mind and Personality
7. Sleep
8. Common Dreams
9. Overall Strength in Life

Each non-empty Dosha characteristic becomes one answer option with a one-mark mapping for that Dosha. Blank cells are omitted and are not inferred.

## Ambiguities

The source contains blank or incomplete cells, including Movement quality/Pitta, Nails/Pitta, Sweating/Vata, Elimination and body odour/Pitta and Kapha, and incomplete wording in Sleep and Behaviour with others. These are not filled by this seed.

## Dīrghāyu Lakṣaṇa

Dīrghāyu is represented separately as Present/Absent questionnaire responses and is excluded from Dosha predictor counts. The document visibly contains 12 signs but refers to items 1–13. The missing thirteenth item is not invented. The document also includes a separate Shorter/Medium/Longer lifespan choice.

## Classification status

The supplied rules specify the broad Eka-Doshaja, Samadoshaja, and Sansargaja/Dwandaja concepts, including the 50%, 25-point, and 30–34% boundaries. The complete published boundary table and tie conditions were not supplied in the repository. Production calculation therefore remains disabled until those rules are verified.
