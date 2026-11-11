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


def upsert_review(
    conn,
    row: dict,
) -> str:
    """Refresh only a newer observation; source IDs remain stable."""
    previous = conn.execute(
        "SELECT source_restaurant_id FROM reviews "
        "WHERE source_code=%s AND source_review_id=%s",
        (row["source_code"], row["source_review_id"]),
    ).fetchone()
    if previous and previous[0] != row["source_restaurant_id"]:
        raise ValueError("A review ID is linked to a different restaurant")
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
            feature_depth_status,
            observed_at,
            raw_object_key
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
            %(feature_depth_status)s,
            %(observed_at)s,
            %(raw_object_key)s
        )
        ON CONFLICT (
            source_code,
            source_review_id
        )
        DO UPDATE SET
            reviewer_id = EXCLUDED.reviewer_id,
            reviewer_name_raw = EXCLUDED.reviewer_name_raw,
            review_title = EXCLUDED.review_title,
            review_text = EXCLUDED.review_text,
            rating = EXCLUDED.rating,
            review_date = EXCLUDED.review_date,
            travel_date = EXCLUDED.travel_date,
            language = EXCLUDED.language,
            device_name = EXCLUDED.device_name,
            total_views = EXCLUDED.total_views,
            total_pictures = EXCLUDED.total_pictures,
            total_likes = EXCLUDED.total_likes,
            total_comments = EXCLUDED.total_comments,
            guest_count = EXCLUDED.guest_count,
            visit_again = EXCLUDED.visit_again,
            money_spend = EXCLUDED.money_spend,
            feature_depth_status = EXCLUDED.feature_depth_status,
            observed_at = EXCLUDED.observed_at,
            raw_object_key = EXCLUDED.raw_object_key
        WHERE reviews.source_restaurant_id = EXCLUDED.source_restaurant_id
          AND (reviews.observed_at IS NULL OR EXCLUDED.observed_at > reviews.observed_at
               OR (EXCLUDED.observed_at = reviews.observed_at
                   AND EXCLUDED.raw_object_key = reviews.raw_object_key))
        """,
        row,
    )

    if result.rowcount == 0:
        return "unchanged"
    return "updated" if previous else "inserted"



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
    updated_reviews = 0
    existing_reviews = 0
    refreshed_ids = set()

    for row in transformed[
        "reviews"
    ]:
        status = upsert_review(conn, row)
        if status == "inserted":
            inserted_reviews += 1
        elif status == "updated":
            updated_reviews += 1
        else:
            existing_reviews += 1
        if status != "unchanged":
            refreshed_ids.add(row["source_review_id"])
            conn.execute(
                "DELETE FROM review_tags WHERE source_code=%s AND source_review_id=%s",
                (row["source_code"], row["source_review_id"]),
            )

    for row in transformed["review_tags"]:
        if row["source_review_id"] in refreshed_ids:
            insert_review_tag(conn, row)

    return {
        "updated_reviews": updated_reviews,
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


def load_versioned_object(conn, transformed, provenance):
    """History ledger and current tables commit together, under a restaurant lock."""
    restaurant = transformed["restaurant"]
    source, restaurant_id = restaurant["source_code"], restaurant["source_restaurant_id"]
    conn.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (f"{source}:{restaurant_id}",))
    previous_version = conn.execute(
        "SELECT code_sha256 FROM data_ingestion_versions "
        "WHERE source_code=%s AND source_restaurant_id=%s AND raw_sha256=%s AND transform_version=%s",
        (source, restaurant_id, provenance["sha256"], provenance["transform_version"]),
    ).fetchone()
    if previous_version:
        if previous_version[0] != provenance["code_sha256"]:
            raise ValueError("Code changed for an existing transform_version; bump TRANSFORM_VERSION")
        return {"inserted_reviews": 0, "updated_reviews": 0,
                "existing_reviews": len(transformed["reviews"]), "version_already_loaded": True}

    current = conn.execute(
        "SELECT crawl_timestamp, raw_object_key FROM restaurants "
        "WHERE source_code=%s AND source_restaurant_id=%s FOR UPDATE",
        (source, restaurant_id),
    ).fetchone()
    incoming_time = restaurant["crawl_timestamp"]
    # Legacy rows have no immutable lineage and used a different naive-time rule.
    # The first versioned import bootstraps them from the selected current raw file.
    legacy_current = current is not None and "/raw_versions/" not in current[1]
    apply_current = current is None or legacy_current or incoming_time >= current[0]
    if (current and incoming_time == current[0] and "/raw_versions/" in current[1]
            and current[1] != provenance["object_name"]):
        raise ValueError("Different snapshots have the same crawl_timestamp; resolve the ordering explicitly")
    if apply_current:
        stats = load_transformed_object(conn, transformed)
    else:
        stats = {"inserted_reviews": 0, "updated_reviews": 0, "existing_reviews": 0,
                 "superseded_reviews": len(transformed["reviews"])}

    conn.execute(
        """INSERT INTO data_ingestion_versions
        (source_code, source_restaurant_id, raw_sha256, transform_version, code_sha256,
         raw_object_key, raw_size_bytes, crawl_timestamp, review_count, applied_to_current)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (source, restaurant_id, provenance["sha256"], provenance["transform_version"],
         provenance["code_sha256"], provenance["object_name"], provenance["size_bytes"],
         incoming_time, len(transformed["reviews"]), apply_current),
    )
    return {**stats, "applied_to_current": apply_current}
