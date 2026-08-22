"""Normalization helpers for tag names."""


def normalize_tag_name(tag: str) -> str:
    cleaned = tag.strip().lower()
    if not cleaned:
        raise ValueError("Tag cannot be empty")
    if len(cleaned) > 100:
        raise ValueError("Tag must be at most 100 characters")
    return cleaned


def normalize_tag_names(tags: list[str] | None) -> list[str]:
    if tags is None:
        return []
    if len(tags) > 5:
        raise ValueError("A photo can have at most 5 tags")
    normalized: list[str] = []
    for tag in tags:
        cleaned = normalize_tag_name(tag)
        if cleaned not in normalized:
            normalized.append(cleaned)
    return normalized
