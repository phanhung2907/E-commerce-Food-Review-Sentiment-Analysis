import re

from datetime import (
    date,
    datetime,
    timezone,
)


SOURCE_CODE = "foody"
FOODY_BASE_URL = (
    "https://www.foody.vn"
)

_FOODY_DATE_RE = re.compile(
    r"/Date\((\d+)"
)


def _text(value):
    if value is None:
        return None

    value = str(value).strip()

    return value or None


def _number(value):
    if value in (
        None,
        "",
    ):
        return None

    try:
        return float(value)
    except (
        TypeError,
        ValueError,
    ):
        return None


def _integer(value):
    if value in (
        None,
        "",
    ):
        return None

    try:
        return int(value)
    except (
        TypeError,
        ValueError,
    ):
        return None


def _first(
    mapping: dict,
    *keys,
):
    for key in keys:
        if (
            key in mapping
            and mapping[key]
            is not None
        ):
            return mapping[key]

    return None


def _absolute_foody_url(
    value,
):
    value = _text(value)

    if not value:
        return None

    if value.startswith(
        ("http://", "https://")
    ):
        return value

    if value.startswith("/"):
        return (
            FOODY_BASE_URL
            + value
        )

    return value


def parse_foody_datetime(
    value,
):
    if value is None:
        return None

    if isinstance(
        value,
        datetime,
    ):
        return value

    text = str(value).strip()

    match = (
        _FOODY_DATE_RE.search(
            text
        )
    )

    if match:
        milliseconds = int(
            match.group(1)
        )

        return datetime.fromtimestamp(
            milliseconds / 1000,
            tz=timezone.utc,
        )

    try:
        parsed = (
            datetime.fromisoformat(
                text.replace(
                    "Z",
                    "+00:00",
                )
            )
        )

        if parsed.tzinfo is None:
            parsed = parsed.replace(
                tzinfo=timezone.utc
            )

        return parsed

    except ValueError:
        return None


def parse_date(value):
    if value is None:
        return None

    if isinstance(value, date):
        return value

    text = str(value).strip()

    for fmt in (
        "%Y-%m-%d",
        "%d/%m/%Y",
    ):
        try:
            return datetime.strptime(
                text,
                fmt,
            ).date()
        except ValueError:
            pass

    return None


def _extract_tags(review: dict):
    raw_tags = (
        review.get("Hashtags")
        or review.get("Tags")
        or []
    )

    if not isinstance(
        raw_tags,
        list,
    ):
        raw_tags = [raw_tags]

    tags = []

    for item in raw_tags:
        if isinstance(item, dict):
            value = _first(
                item,
                "Name",
                "Text",
                "TagName",
                "Title",
                "name",
                "text",
                "tag",
            )
        else:
            value = item

        value = _text(value)

        if value:
            tags.append(value)

    return sorted(set(tags))


def _extract_cuisines(
    restaurant: dict,
):
    raw = _first(
        restaurant,
        "cuisines",
        "Cuisines",
        "cuisine",
        "Cuisine",
    )

    if raw is None:
        return []

    if isinstance(raw, list):
        values = raw
    else:
        values = str(raw).split(",")

    output = []

    for item in values:
        if isinstance(item, dict):
            value = _first(
                item,
                "name",
                "Name",
                "title",
                "Title",
            )
        else:
            value = item

        value = _text(value)

        if value:
            output.append(value)

    return sorted(set(output))


_DAY_MAP = {
    "monday": 1,
    "mon": 1,
    "tuesday": 2,
    "tue": 2,
    "wednesday": 3,
    "wed": 3,
    "thursday": 4,
    "thu": 4,
    "friday": 5,
    "fri": 5,
    "saturday": 6,
    "sat": 6,
    "sunday": 7,
    "sun": 7,
}


def _time_text(value):
    value = _text(value)

    if not value:
        return None

    # PostgreSQL accepts HH:MM and HH:MM:SS.
    return value


def _extract_opening_hours(
    restaurant: dict,
):
    raw = _first(
        restaurant,
        "opening_hours",
        "OpeningHours",
        "openingHoursSpecification",
    )

    if not isinstance(raw, list):
        return []

    rows = []

    for item in raw:
        if not isinstance(
            item,
            dict,
        ):
            continue

        raw_day = _first(
            item,
            "day_of_week",
            "dayOfWeek",
            "DayOfWeek",
            "day",
            "Day",
        )

        if isinstance(
            raw_day,
            list,
        ):
            days = raw_day
        else:
            days = [raw_day]

        for day in days:
            if isinstance(day, int):
                day_num = day
            else:
                day_text = (
                    _text(day)
                    or ""
                )

                day_text = (
                    day_text
                    .split("/")[-1]
                    .lower()
                )

                day_num = (
                    _DAY_MAP.get(
                        day_text
                    )
                )

            if (
                day_num is None
                or not 1 <= day_num <= 7
            ):
                continue

            rows.append({
                "day_of_week":
                    day_num,
                "open_time":
                    _time_text(
                        _first(
                            item,
                            "open_time",
                            "opens",
                            "open",
                        )
                    ),
                "close_time":
                    _time_text(
                        _first(
                            item,
                            "close_time",
                            "closes",
                            "close",
                        )
                    ),
            })

    # Current database design stores one period/day.
    # Keep first unique day.
    unique = {}

    for row in rows:
        unique.setdefault(
            row["day_of_week"],
            row,
        )

    return list(
        unique.values()
    )


def transform_foody_object(
    raw: dict,
    object_name: str,
) -> dict:
    raw_source = (
        raw.get("source")
    )

    if (
        raw_source is not None
        and str(raw_source).strip()
        != SOURCE_CODE
    ):
        raise ValueError(
            "Raw source mismatch: "
            f"{raw_source!r}"
        )

    restaurant = (
        raw.get("restaurant")
        or {}
    )

    source_restaurant_id = (
        _first(
            restaurant,
            "restaurant_id",
            "ResId",
            "Id",
        )
    )

    if source_restaurant_id is None:
        raise ValueError(
            "Thiếu restaurant_id"
        )

    source_restaurant_id = str(
        source_restaurant_id
    ).strip()

    crawl_timestamp = (
        parse_foody_datetime(
            raw.get(
                "crawl_timestamp"
            )
        )
        or datetime.now(
            timezone.utc
        )
    )

    restaurant_row = {
        "source_code":
            SOURCE_CODE,
        "source_restaurant_id":
            source_restaurant_id,
        "name":
            _text(
                _first(
                    restaurant,
                    "name",
                    "Name",
                )
            ),
        "url":
            _absolute_foody_url(
                _first(
                    restaurant,
                    "url",
                    "Url",
                )
            ),
        "city":
            _text(
                _first(
                    restaurant,
                    "city",
                    "City",
                )
            ),
        "address":
            _text(
                _first(
                    restaurant,
                    "address",
                    "Address",
                )
            ),
        "category":
            _text(
                _first(
                    restaurant,
                    "category",
                    "Category",
                )
            ),
        "location":
            _text(
                _first(
                    restaurant,
                    "location",
                    "Location",
                )
            ),
        "avg_rating":
            _number(
                _first(
                    restaurant,
                    "avg_rating",
                    "AvgRating",
                )
            ),
        # Do NOT use review_summary.total_reviews_api:
        # Foody may cap it at 100.
        "total_reviews":
            _integer(
                _first(
                    restaurant,
                    "total_reviews",
                    "TotalReviews",
                    "ReviewCount",
                )
            ),
        "latitude":
            _number(
                _first(
                    restaurant,
                    "latitude",
                    "Latitude",
                )
            ),
        "longitude":
            _number(
                _first(
                    restaurant,
                    "longitude",
                    "Longitude",
                )
            ),
        "price_range":
            _text(
                _first(
                    restaurant,
                    "price_range",
                    "PriceRange",
                )
            ),
        "telephone":
            _text(
                _first(
                    restaurant,
                    "telephone",
                    "Telephone",
                    "phone",
                    "Phone",
                )
            ),
        "crawl_timestamp":
            crawl_timestamp,
        "raw_object_key":
            object_name,
    }

    opening_hours = []

    for item in (
        _extract_opening_hours(
            restaurant
        )
    ):
        opening_hours.append({
            "source_code":
                SOURCE_CODE,
            "source_restaurant_id":
                source_restaurant_id,
            **item,
        })

    cuisines = [
        {
            "source_code":
                SOURCE_CODE,
            "source_restaurant_id":
                source_restaurant_id,
            "cuisine":
                cuisine,
        }
        for cuisine in (
            _extract_cuisines(
                restaurant
            )
        )
    ]

    reviewer_rows = {}
    review_rows = []
    tag_rows = []

    for review in (
        raw.get("reviews")
        or []
    ):
        if not isinstance(
            review,
            dict,
        ):
            continue

        review_id = (
            _first(
                review,
                "Id",
                "id",
                "review_id",
            )
        )

        if review_id is None:
            continue

        source_review_id = str(
            review_id
        ).strip()

        owner = (
            review.get("Owner")
            or {}
        )

        reviewer_id = (
            owner.get("Id")
        )

        reviewer_name = (
            _text(
                owner.get(
                    "DisplayName"
                )
            )
            or _text(
                owner.get(
                    "Username"
                )
            )
        )

        if reviewer_id is not None:
            reviewer_id = str(
                reviewer_id
            ).strip()

            reviewer_rows[
                reviewer_id
            ] = {
                "source_code":
                    SOURCE_CODE,
                "reviewer_id":
                    reviewer_id,
                "reviewer_name":
                    reviewer_name,
                "total_reviews":
                    _integer(
                        owner.get(
                            "TotalReviews"
                        )
                    ),
                "total_pictures":
                    _integer(
                        owner.get(
                            "TotalPictures"
                        )
                    ),
                "trust_percent":
                    _number(
                        owner.get(
                            "TrustPercent"
                        )
                    ),
                "verifying_percent":
                    _number(
                        owner.get(
                            "VerifyingPercent"
                        )
                    ),
                "is_verified":
                    owner.get(
                        "IsVerified"
                    ),
            }

            reviewer_name_raw = None
        else:
            reviewer_name_raw = (
                reviewer_name
            )

        options = (
            review.get("Options")
            or {}
        )

        review_rows.append({
            "source_code":
                SOURCE_CODE,
            "source_review_id":
                source_review_id,
            "source_restaurant_id":
                source_restaurant_id,
            "reviewer_id":
                reviewer_id,
            "reviewer_name_raw":
                reviewer_name_raw,
            "review_title":
                _text(
                    _first(
                        review,
                        "Title",
                        "title",
                    )
                ),
            "review_text":
                _text(
                    _first(
                        review,
                        "Description",
                        "description",
                        "review_text",
                    )
                ),
            "rating":
                _number(
                    _first(
                        review,
                        "AvgRating",
                        "rating",
                        "Rating",
                    )
                ),
            "review_date":
                parse_foody_datetime(
                    _first(
                        review,
                        "CreatedDate",
                        "review_date",
                    )
                ),
            "travel_date":
                parse_date(
                    _first(
                        review,
                        "travel_date",
                        "TravelDate",
                    )
                ),
            "language":
                _text(
                    _first(
                        review,
                        "language",
                        "Language",
                    )
                ),
            "device_name":
                _text(
                    _first(
                        review,
                        "DeviceName",
                        "device_name",
                    )
                ),
            "total_views":
                _integer(
                    _first(
                        review,
                        "TotalViews",
                        "TotalView",
                    )
                ),
            "total_pictures":
                _integer(
                    _first(
                        review,
                        "TotalPictures",
                        "total_pictures",
                    )
                ),
            "total_likes":
                _integer(
                    _first(
                        review,
                        "TotalLike",
                        "TotalLikes",
                    )
                ),
            "total_comments":
                _integer(
                    _first(
                        review,
                        "TotalComment",
                        "TotalComments",
                    )
                ),
            "guest_count":
                _text(
                    options.get(
                        "Guest"
                    )
                ),
            "visit_again":
                _text(
                    options.get(
                        "VisitAgain"
                    )
                ),
            "money_spend":
                _text(
                    options.get(
                        "MoneySpend"
                    )
                ),
            "feature_depth_status":
                _text(
                    review.get(
                        "feature_depth_status"
                    )
                ),
        })

        for tag in _extract_tags(
            review
        ):
            tag_rows.append({
                "source_code":
                    SOURCE_CODE,
                "source_review_id":
                    source_review_id,
                "tag":
                    tag,
            })

    return {
        "restaurant":
            restaurant_row,
        "opening_hours":
            opening_hours,
        "cuisines":
            cuisines,
        "reviewers":
            list(
                reviewer_rows.values()
            ),
        "reviews":
            review_rows,
        "review_tags":
            tag_rows,
    }
