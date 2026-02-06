from __future__ import annotations

import re

TAG_RE = re.compile(r"(?<!\w)#([A-Za-z0-9][A-Za-z0-9_-]*)")
MENTION_RE = re.compile(r"(?<!\w)@([A-Za-z0-9][A-Za-z0-9_-]*)")
ALLOWED_MENTIONS = {"leo", "victor", "clems"}


def parse_tags(text: str) -> list[str]:
    tags = {match.group(1).lower() for match in TAG_RE.finditer(text)}
    return sorted(tags)


def parse_mentions(text: str) -> list[str]:
    mentions = {match.group(1).lower() for match in MENTION_RE.finditer(text)}
    return sorted([m for m in mentions if m in ALLOWED_MENTIONS])
