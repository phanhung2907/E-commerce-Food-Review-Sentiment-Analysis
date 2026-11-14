"""Map the observed TripAdvisor and Eatigo JSON shapes into PostgreSQL rows."""
from datetime import date, datetime, time, timedelta, timezone

VIETNAM = timezone(timedelta(hours=7))
DAYS = {name: i for i, name in enumerate(
    ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"), 1
)}


def text(value):
    if value is None:
        return None
    value = str(value).replace("\x00", "").strip()
    return value or None


def identifier(value):
    result = text(value)
    if result is None:
        raise ValueError("Missing source identifier")
    return result


def timestamp(value):
    value = text(value)
    if value is None:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return (parsed if parsed.tzinfo else parsed.replace(tzinfo=VIETNAM)).isoformat()


def travel_date(value):
    value = text(value)
    if value is None or value.lower() in {"recent", "n/a", "na", "unknown"}:
        return None
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        return None


def number(value):
    if value is None or str(value).strip().lower() in {"", "n/a", "na", "none", "null", "nan"}:
        return None
    return str(value)


def crawl_time(owner, data):
    if owner == "tuan":
        from tuan import record_crawl_time

        observed = (record_crawl_time(row) for row in data)
        return max(filter(None, observed), key=datetime.fromisoformat, default=None)
    if owner == "sang":
        return timestamp(data["crawl_timestamp"])
    return max((timestamp(row["crawl_timestamp"]) for row in data["reviews"]
                if row.get("crawl_timestamp")), default=None)


def transform(owner, data, key, file_modified_at):
    if owner == "tuan":
        from tuan import transform_tuan

        return transform_tuan(data, key, file_modified_at)
    reviews = data["reviews"]
    crawl = crawl_time(owner, data) or file_modified_at
    if owner == "kien":
        source = "tripadvisor"
        metadata = data.get("metadata") or {}
        address = metadata.get("address") or {}
        rating = metadata.get("aggregateRating") or {}
        geo = metadata.get("geo") or {}
        restaurant_id = identifier(data["restaurant_id"])
        restaurant = dict(name=text(data.get("restaurant_name")),
                          url=text(data.get("restaurant_url")), city=text(data.get("city")),
                          address=text(address.get("streetAddress") if isinstance(address, dict) else address),
                          avg_rating=number(rating.get("ratingValue")),
                          total_reviews=number(rating.get("reviewCount")) or len(reviews),
                          latitude=number(geo.get("latitude")), longitude=number(geo.get("longitude")),
                          price_range=text(metadata.get("priceRange")),
                          telephone=text(metadata.get("telephone")))
    else:
        source = "eatigo"
        raw = data["restaurant"]
        restaurant_id = identifier(raw["restaurant_id"])
        tags = data.get("restaurant_tags_raw") or {}
        restaurant = dict(name=text(raw.get("name")), city=text(raw.get("city")),
                          address=text(raw.get("address")),
                          url=text(raw.get("url")),
                          total_reviews=number(tags.get("total_reviews_count")) or len(reviews))

    restaurant_key = dict(source_code=source, source_restaurant_id=restaurant_id)
    batches = {"restaurants": [dict(restaurant, **restaurant_key, crawl_timestamp=crawl,
                                    raw_object_key=key)],
               "reviewers": [], "reviews": [], "review_tags": [],
               "restaurant_cuisines": [], "restaurant_opening_hours": []}
    if owner == "kien":
        cuisines = metadata.get("servesCuisine") or []
        if isinstance(cuisines, str):
            cuisines = [] if cuisines.strip().lower() in {"n/a", "na", ""} else [cuisines]
        for cuisine in cuisines:
            if text(cuisine):
                batches["restaurant_cuisines"].append(dict(restaurant_key, cuisine=text(cuisine)))
        hours = metadata.get("openingHoursSpecification")
        for item in hours if isinstance(hours, list) else []:
            day = DAYS.get(str(item.get("dayOfWeek", "")).rsplit("/", 1)[-1])
            if day and item.get("opens") and item.get("closes"):
                batches["restaurant_opening_hours"].append(dict(
                    restaurant_key, day_of_week=day,
                    open_time=time.fromisoformat(item["opens"]).isoformat(),
                    close_time=time.fromisoformat(item["closes"]).isoformat(),
                ))
    for raw in reviews:
        if owner == "kien":
            if identifier(raw["restaurant_id"]) != restaurant_id:
                raise ValueError("Review restaurant ID differs from its parent")
            review_id = identifier(raw["review_id"])
            reviewer_id = text(raw.get("reviewer_id"))
            if reviewer_id:
                batches["reviewers"].append(dict(source_code=source, reviewer_id=reviewer_id))
            review = dict(reviewer_id=reviewer_id, review_title=text(raw.get("review_title")),
                          review_text=text(raw.get("review_text")),
                          review_date=timestamp(raw.get("review_date")),
                          travel_date=travel_date(raw.get("travel_date")),
                          feature_depth_status=text(raw.get("feature_depth_status")))
        else:
            review_id = identifier(raw["id"])
            review = dict(reviewer_name_raw=text(raw.get("rated_by")),
                          review_text=text(raw.get("description")),
                          review_date=timestamp(raw.get("comment_time")),
                          total_likes=number(raw.get("like_count")))
            for tag in raw.get("tags") or []:
                name = text(tag["name"])
                if name:
                    batches["review_tags"].append(dict(source_code=source,
                                                       source_review_id=review_id, tag=name))
        batches["reviews"].append(dict(review, **restaurant_key, source_review_id=review_id,
                                       rating=number(raw.get("rating"))))
    return batches

