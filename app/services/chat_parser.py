from __future__ import annotations

import re

TAG_RE = re.compile(r"(?<!\w)#([A-Za-z0-9][A-Za-z0-9_-]*)")
MENTION_RE = re.compile(r"(?<!\w)@([A-Za-z0-9][A-Za-z0-9_-]*)")
AGENT_ID_RE = re.compile(r"^agent-(\d+)$")
ALLOWED_MENTIONS = {"leo", "victor", "nova", "vulgarisation", "clems", "clem"}


def parse_tags(text: str) -> list[str]:
    tags = {match.group(1).lower() for match in TAG_RE.finditer(text)}
    return sorted(tags)


def parse_mentions(text: str) -> list[str]:
    mentions = {match.group(1).lower() for match in MENTION_RE.finditer(text)}
    normalized: set[str] = set()
    for mention in mentions:
        if mention in ALLOWED_MENTIONS:
            normalized.add("clems" if mention == "clem" else mention)
            continue
        if AGENT_ID_RE.match(mention):
            normalized.add(mention)
    return sorted(normalized)
