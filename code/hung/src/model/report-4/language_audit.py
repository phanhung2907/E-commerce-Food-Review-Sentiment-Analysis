"""Extract the review body and check the language recorded in the snapshot."""

import re

from lingua import Language, LanguageDetectorBuilder

from text_features import clean_text

LANGUAGE_LABELS = {
    "vi": Language.VIETNAMESE, "en": Language.ENGLISH,
    "ja": Language.JAPANESE, "fr": Language.FRENCH,
}
DETECTOR = LanguageDetectorBuilder.from_all_languages().with_low_accuracy_mode().build()
TRIP_DATE = re.compile(
    r"(?im)^(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})"
    r"(?:[ \t]+•[^\n]*)?[ \t]*$"
)
TRIP_FOOTER = re.compile(
    r"(?im)^(?:Written [^\n]+|Translated from [^\n]+|Show original|"
    r"This review is the subjective opinion[^\n]*)[ \t]*$"
)
TRIP_TAGS = re.compile(r"(?im)^(?:Value|Service|Food|Atmosphere)[ \t]*$")
JA_SCRIPT = re.compile(r"[\u3040-\u30ff]")


def review_body(text, source):
    if source == "tripadvisor":
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        header = TRIP_DATE.search(text[:1000])
        footer = TRIP_FOOTER.search(text, header.end() if header else 0)
        text = text[header.end() if header else 0:footer.start() if footer else len(text)]
        text = TRIP_TAGS.sub("", text)
        if not header:
            text = re.sub(r"(?is)^.{0,500}?\bcontributions?\s*\n\d+\s*\n[^\n]*\n", "", text)
    return clean_text(text)


def classify_scores(scores, label):
    best, second = scores[:2]
    expected = LANGUAGE_LABELS[label]
    identified = best.language.iso_code_639_1.name.lower()
    if best.language == expected:
        return "accepted", identified
    expected_score = next(score.value for score in scores if score.language == expected)
    if (best.value >= 0.75 and best.value - second.value >= 0.25 and expected_score <= 0.10):
        return "language_mismatch", identified
    return "uncertain", identified


def audit_language(rows, label):
    """Apply one detector in parallel to bounded batches of reviews."""
    for start in range(0, len(rows), 4096):
        batch = rows[start:start + 4096]
        needs_detection = []
        for row in batch:
            text = row["text"]
            if label == "ja" and JA_SCRIPT.search(text):
                row.update(language_status="accepted", detected_language="ja")
            elif sum(character.isalpha() for character in text) < 12:
                row.update(language_status="short_uncertain", detected_language="")
            else:
                needs_detection.append(row)
        texts = [row["text"][:1200] for row in needs_detection]
        scores = DETECTOR.compute_language_confidence_values_in_parallel(texts)
        for row, confidence in zip(needs_detection, scores, strict=True):
            status, detected = classify_scores(confidence, label)
            row.update(language_status=status, detected_language=detected)
