import re
import json
from playwright.sync_api import sync_playwright

URL = "https://www.ubereats.com/store/burger-king-819-van-ness-avenue/4AKFDnViSneI-atUGcXLLg?diningMode=DELIVERY"

DATE_RE = re.compile(r"\d{2}/\d{2}/\d{2}")

def parse_reviews(text: str):
    lines = [x.strip(" •\t") for x in text.splitlines() if x.strip()]

    reviews = []

    for i, line in enumerate(lines):
        if not DATE_RE.fullmatch(line):
            continue

        if i == 0 or i + 1 >= len(lines):
            continue

        reviewer = lines[i - 1]
        comment = lines[i + 1]

        reviews.append({
            "reviewer": reviewer,
            "date": line,
            "comment": comment
        })

    return reviews


with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False
    )

    page = browser.new_page(
        viewport={"width": 1440, "height": 1200}
    )

    page.goto(
        URL,
        wait_until="domcontentloaded",
        timeout=60_000
    )

    # Chờ trang render
    page.wait_for_timeout(3000)

    # Scroll tới phần review
    review_heading = page.get_by_text(
        "Rating and reviews",
        exact=True
    ).first

    review_heading.scroll_into_view_if_needed()
    page.wait_for_timeout(1000)

    # Click See more nếu có
    see_more = page.get_by_text(
        "See more",
        exact=True
    )

    if see_more.count() > 0:
        try:
            see_more.first.click()
            page.wait_for_timeout(1500)
        except:
            pass

    # Lấy text toàn page
    body_text = page.locator("body").inner_text()

    # Chỉ giữ phần từ Rating and reviews trở đi
    marker = "43 Reviews"

    if marker in body_text:
        review_text = body_text.split(marker, 1)[1]
    else:
        review_text = body_text

    reviews = parse_reviews(review_text)

    print(f"Found: {len(reviews)} reviews")

    for r in reviews[:5]:
        print(r)

    with open(
        "uber_reviews.json",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            reviews,
            f,
            ensure_ascii=False,
            indent=2
        )

    browser.close()