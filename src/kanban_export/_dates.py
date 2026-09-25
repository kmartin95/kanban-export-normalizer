"""Shared timestamp parsing for the parsers that use it.

Asana's and GitHub's APIs both return ISO 8601 with a trailing "Z", which
datetime.fromisoformat only accepts from Python 3.11 onward; this project
targets 3.10, so we swap "Z" for an explicit offset first. Jira's CSV
export doesn't use ISO 8601 at all - the "Created"/"Resolved" columns are
formatted according to the exporting user's locale and date settings, so
there's no single format guaranteed to match. We try the handful of
formats Jira commonly uses and give up silently (returning None) rather
than raising, since a card missing a timestamp is a normal, expected case
across every one of these formats.
"""

from datetime import datetime
from typing import Optional


def parse_iso_datetime(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


_JIRA_DATETIME_FORMATS = (
    "%d/%b/%y %I:%M %p",
    "%d/%b/%Y %I:%M %p",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%dT%H:%M:%S.%f%z",
)


def parse_jira_datetime(value: str) -> Optional[datetime]:
    if not value:
        return None
    for fmt in _JIRA_DATETIME_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return parse_iso_datetime(value)
