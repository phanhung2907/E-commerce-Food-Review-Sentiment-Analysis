import requests
import json
from typing import Any

url = "https://www.foody.vn/__get/Review/ResLoadMore"

params = {
    "t": "1758290000000",
    "ResId": 663638,
    "LastId": 0,
    "Count": 20,
    "Type": 1,
    "isLatest": "true"
}

headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.foody.vn/binh-dinh/chat-cafe-hoang-dieu",
    "X-Requested-With": "XMLHttpRequest"
}


# =========================
# 1. GỌI API
# =========================

response = requests.get(
    url,
    params=params,
    headers=headers,
    timeout=30
)

print("HTTP:", response.status_code)
response.raise_for_status()

data = response.json()

print("ROOT TYPE:", type(data).__name__)

if isinstance(data, dict):
    print("ROOT KEYS:", list(data.keys()))

print("\n" + "=" * 80)


# =========================
# 2. IN JSON RAW
# =========================

print("RAW RESPONSE:")
print(
    json.dumps(
        data,
        ensure_ascii=False,
        indent=2
    )[:5000]
)

print("\n" + "=" * 80)


# =========================
# 3. HÀM LẤY TOÀN BỘ FEATURE
# =========================

def extract_features(
    obj: Any,
    path: str = "",
    features: dict | None = None
):
    """
    Duyệt recursive toàn bộ JSON.

    Ví dụ output:
    Owner.Id
    Owner.DisplayName
    Restaurant.Name
    Pictures[].Url
    """

    if features is None:
        features = {}

    # -------------------------
    # Dictionary
    # -------------------------
    if isinstance(obj, dict):

        if path:
            features.setdefault(
                path,
                {
                    "type": "dict",
                    "example": None
                }
            )

        for key, value in obj.items():

            new_path = (
                f"{path}.{key}"
                if path
                else key
            )

            extract_features(
                value,
                new_path,
                features
            )

    # -------------------------
    # List
    # -------------------------
    elif isinstance(obj, list):

        list_path = f"{path}[]"

        features.setdefault(
            list_path,
            {
                "type": "list",
                "example": f"{len(obj)} items"
            }
        )

        # Duyệt TẤT CẢ phần tử,
        # không chỉ phần tử đầu tiên
        for item in obj:
            extract_features(
                item,
                list_path,
                features
            )

    # -------------------------
    # Leaf value
    # -------------------------
    else:

        if obj is None:
            value_type = "NoneType"
        else:
            value_type = type(obj).__name__

        if path not in features:
            features[path] = {
                "type": value_type,
                "example": obj
            }

        else:
            # Một field đôi khi có nhiều kiểu
            old_type = features[path]["type"]

            if value_type not in old_type.split(" | "):
                features[path]["type"] += f" | {value_type}"

            # Nếu example cũ None thì lấy value mới
            if features[path]["example"] is None and obj is not None:
                features[path]["example"] = obj

    return features


# =========================
# 4. EXTRACT TOÀN RESPONSE
# =========================

features = extract_features(data)


print("TOÀN BỘ SCHEMA")
print("=" * 80)

for index, (field, info) in enumerate(
    sorted(features.items()),
    start=1
):
    example = info["example"]

    # rút ngắn ví dụ quá dài
    example_str = repr(example)

    if len(example_str) > 100:
        example_str = example_str[:97] + "..."

    print(
        f"{index:03}. "
        f"{field:<60} "
        f"{info['type']:<20} "
        f"{example_str}"
    )


# =========================
# 5. CHỈ LẤY LEAF FEATURES
# =========================

leaf_features = {
    field: info
    for field, info in features.items()
    if info["type"] not in ["dict", "list"]
}


print("\n" + "=" * 80)
print("LEAF FEATURES")
print("=" * 80)

for index, (field, info) in enumerate(
    sorted(leaf_features.items()),
    start=1
):

    example_str = repr(info["example"])

    if len(example_str) > 100:
        example_str = example_str[:97] + "..."

    print(
        f"{index:03}. "
        f"{field:<60} "
        f"{info['type']:<20} "
        f"{example_str}"
    )


print("\n" + "=" * 80)
print("THỐNG KÊ")
print("=" * 80)

print("Tổng node trong JSON :", len(features))
print("Tổng leaf features   :", len(leaf_features))


# =========================
# 6. LƯU SCHEMA RA JSON
# =========================

schema_output = {
    field: info
    for field, info in sorted(features.items())
}

with open(
    "foody_schema.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        schema_output,
        f,
        ensure_ascii=False,
        indent=2,
        default=str
    )


print("\nĐã lưu schema vào: foody_schema.json")