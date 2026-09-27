from minio_client import (
    MINIO_BUCKET,
    MINIO_ENDPOINT,
    create_bucket_if_missing,
    create_minio_client,
)


def main():
    client = create_minio_client()

    created = create_bucket_if_missing(
        client
    )

    print(
        "MinIO endpoint:",
        MINIO_ENDPOINT,
    )

    if created:
        print(
            "Created bucket:",
            MINIO_BUCKET,
        )
    else:
        print(
            "Bucket already exists:",
            MINIO_BUCKET,
        )


if __name__ == "__main__":
    main()
