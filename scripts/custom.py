import hashlib


def compute_checksum(text: str | None) -> str:
    checksum = hashlib.md5(f"{text}".encode("utf-8")).hexdigest()
    return checksum


def get_unique_identifier_from_doccano_data(d: dict) -> str:
    _id = d.get("id")
    checksum = compute_checksum(d.get("text"))
    return f"{_id}_{checksum}"


def get_unique_identifier_from_raw_data(d: dict) -> str:
    _id = d.get("id")
    checksum = compute_checksum(d.get("text"))
    return f"{_id}_{checksum}"


def transform_raw_data_to_doccano_data(d: dict) -> dict:
    return d


def transform_doccano_data_to_annotated_data(d: dict) -> dict:
    annotations = [
        {
            "start": a[0],
            "end": a[1],
            "label": a[2],
        }
        for a in d.get("label", [])
    ]
    return {
        "id": get_unique_identifier_from_doccano_data(d=d),
        "checksum": compute_checksum(d.get("text")),
        "annotations": annotations,
        # "timestamp": EXTRACT_TIME,
    }
