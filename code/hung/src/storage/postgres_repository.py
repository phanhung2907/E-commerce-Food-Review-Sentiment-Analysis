def ensure_source_exists(
    conn,
    source_code: str,
) -> None:
    row = conn.execute(
        """
        SELECT 1
        FROM sources
        WHERE source_code = %s
        """,
        (source_code,),
    ).fetchone()

    if row is None:
        raise ValueError(
            "Source chưa tồn tại trong "
            f"database: {source_code}"
        )


def upsert_restaurant(
    conn,
    row: dict,
) -> None:
    conn.execute(
        """
        INSERT INTO restaurants (
            source_code,
            source_restaurant_id,
            name,
            url,
            city,
            address,
            category,
            location,
            avg_rating,
            total_reviews,
            latitude,
            longitude,
            price_range,
            telephone,
            crawl_timestamp,
            raw_object_key
        )
        VALUES (
            %(source_code)s,
            %(source_restaurant_id)s,
            %(name)s,
            %(url)s,
            %(city)s,
            %(address)s,
            %(category)s,
            %(location)s,
            %(avg_rating)s,
            %(total_reviews)s,
            %(latitude)s,
            %(longitude)s,
            %(price_range)s,
            %(telephone)s,
            %(crawl_timestamp)s,
            %(raw_object_key)s
        )
        ON CONFLICT (
            source_code,
            source_restaurant_id
        )
        DO UPDATE SET
            name =
                COALESCE(
                    EXCLUDED.name,
                    restaurants.name
                ),
            url =
                COALESCE(
                    EXCLUDED.url,
                    restaurants.url
                ),
            city =
                COALESCE(
                    EXCLUDED.city,
                    restaurants.city
                ),
            address =
                COALESCE(
                    EXCLUDED.address,
                    restaurants.address
                ),
            category =
                COALESCE(
                    EXCLUDED.category,
                    restaurants.category
                ),
            location =
                COALESCE(
                    EXCLUDED.location,
                    restaurants.location
                ),
            avg_rating =
                COALESCE(
                    EXCLUDED.avg_rating,
                    restaurants.avg_rating
                ),
            total_reviews =
                COALESCE(
                    EXCLUDED.total_reviews,
                    restaurants.total_reviews
                ),
            latitude =
                COALESCE(
                    EXCLUDED.latitude,
                    restaurants.latitude
                ),
            longitude =
                COALESCE(
                    EXCLUDED.longitude,
                    restaurants.longitude
                ),
            price_range =
                COALESCE(
                    EXCLUDED.price_range,
                    restaurants.price_range
                ),
            telephone =
                COALESCE(
                    EXCLUDED.telephone,
                    restaurants.telephone
                ),
            crawl_timestamp =
                EXCLUDED.crawl_timestamp,
            raw_object_key =
                EXCLUDED.raw_object_key
        """,
        row,
    )


def upsert_opening_hour(
    conn,
    row: dict,
) -> None:
    conn.execute(
        """
        INSERT INTO
            restaurant_opening_hours (
                source_code,
                source_restaurant_id,
                day_of_week,
                open_time,
                close_time
            )
        VALUES (
            %(source_code)s,
            %(source_restaurant_id)s,
            %(day_of_week)s,
            %(open_time)s,
            %(close_time)s
        )
        ON CONFLICT (
            source_code,
            source_restaurant_id,
            day_of_week
        )
        DO UPDATE SET
            open_time =
                EXCLUDED.open_time,
            close_time =
                EXCLUDED.close_time
        """,
        row,
    )


def insert_cuisine(
    conn,
    row: dict,
) -> None:
    conn.execute(
        """
        INSERT INTO restaurant_cuisines (
            source_code,
            source_restaurant_id,
            cuisine
        )
        VALUES (
            %(source_code)s,
            %(source_restaurant_id)s,
            %(cuisine)s
        )
        ON CONFLICT DO NOTHING
        """,
        row,
    )


def upsert_reviewer(
    conn,
    row: dict,
) -> None:
    conn.execute(
        """
        INSERT INTO reviewers (
            source_code,
            reviewer_id,
            reviewer_name,
            total_reviews,
            total_pictures,
            trust_percent,
            verifying_percent,
            is_verified
        )
        VALUES (
            %(source_code)s,
            %(reviewer_id)s,
            %(reviewer_name)s,
            %(total_reviews)s,
            %(total_pictures)s,
            %(trust_percent)s,
            %(verifying_percent)s,
            %(is_verified)s
        )
        ON CONFLICT (
            source_code,
            reviewer_id
        )
        DO UPDATE SET
            reviewer_name =
                COALESCE(
                    EXCLUDED.reviewer_name,
                    reviewers.reviewer_name
                ),
            total_reviews =
                COALESCE(
                    EXCLUDED.total_reviews,
                    reviewers.total_reviews
                ),
            total_pictures =
                COALESCE(
                    EXCLUDED.total_pictures,
                    reviewers.total_pictures
                ),
            trust_percent =
                COALESCE(
                    EXCLUDED.trust_percent,
                    reviewers.trust_percent
                ),
            verifying_percent =
                COALESCE(
                    EXCLUDED.verifying_percent,
                    reviewers.verifying_percent
                ),
            is_verified =
                COALESCE(
                    EXCLUDED.is_verified,
                    reviewers.is_verified
                )
        """,
        row,
    )


def insert_review_if_new(
    conn,
    row: dict,
) -> bool:
    """
    Database-level idempotency:
    (source_code, source_review_id)
    already exists -> DO NOTHING.
    """
    result = conn.execute(
        """
        INSERT INTO reviews (
            source_code,
            source_review_id,
            source_restaurant_id,
            reviewer_id,
            reviewer_name_raw,
            review_title,
            review_text,
            rating,
            review_date,
            travel_date,
            language,
            device_name,
            total_views,
            total_pictures,
            total_likes,
            total_comments,
            guest_count,
            visit_again,
            money_spend,
            feature_depth_status
        )
        VALUES (
            %(source_code)s,
            %(source_review_id)s,
            %(source_restaurant_id)s,
            %(reviewer_id)s,
            %(reviewer_name_raw)s,
            %(review_title)s,
            %(review_text)s,
            %(rating)s,
            %(review_date)s,
            %(travel_date)s,
            %(language)s,
            %(device_name)s,
            %(total_views)s,
            %(total_pictures)s,
            %(total_likes)s,
            %(total_comments)s,
            %(guest_count)s,
            %(visit_again)s,
            %(money_spend)s,
            %(feature_depth_status)s
        )
        ON CONFLICT (
            source_code,
            source_review_id
        )
        DO NOTHING
        """,
        row,
    )

    return result.rowcount == 1


def insert_review_tag(
    conn,
    row: dict,
) -> None:
    conn.execute(
        """
        INSERT INTO review_tags (
            source_code,
            source_review_id,
            tag
        )
        VALUES (
            %(source_code)s,
            %(source_review_id)s,
            %(tag)s
        )
        ON CONFLICT DO NOTHING
        """,
        row,
    )


def load_transformed_object(
    conn,
    transformed: dict,
) -> dict:
    source_code = (
        transformed[
            "restaurant"
        ][
            "source_code"
        ]
    )

    ensure_source_exists(
        conn,
        source_code,
    )

    upsert_restaurant(
        conn,
        transformed[
            "restaurant"
        ],
    )

    for row in transformed[
        "opening_hours"
    ]:
        upsert_opening_hour(
            conn,
            row,
        )

    for row in transformed[
        "cuisines"
    ]:
        insert_cuisine(
            conn,
            row,
        )

    for row in transformed[
        "reviewers"
    ]:
        upsert_reviewer(
            conn,
            row,
        )

    inserted_reviews = 0
    existing_reviews = 0

    for row in transformed[
        "reviews"
    ]:
        inserted = (
            insert_review_if_new(
                conn,
                row,
            )
        )

        if inserted:
            inserted_reviews += 1
        else:
            existing_reviews += 1

    for row in transformed[
        "review_tags"
    ]:
        insert_review_tag(
            conn,
            row,
        )

    return {
        "inserted_reviews":
            inserted_reviews,
        "existing_reviews":
            existing_reviews,
        "reviewers":
            len(
                transformed[
                    "reviewers"
                ]
            ),
        "tags":
            len(
                transformed[
                    "review_tags"
                ]
            ),
    }
