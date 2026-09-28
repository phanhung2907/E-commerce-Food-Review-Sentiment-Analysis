SOURCE_CODES = frozenset({
    "foody",
    "tripadvisor",
    "eatigo",
    "capichi",
})


def validate_source_code(source_code: str) -> str:
    """
    Validate canonical source labels.

    Source labels are deliberately strict because they participate in
    database primary/foreign keys and downstream grouping.
    """
    value = str(source_code).strip()

    if value not in SOURCE_CODES:
        allowed = ", ".join(sorted(SOURCE_CODES))
        raise ValueError(
            f"source_code không hợp lệ: {value!r}. "
            f"Chỉ chấp nhận: {allowed}"
        )

    return value
