"""Parser for GitHub Projects (the v2, org/user-level kind) fetched via the
GraphQL API - there is no "export" button in the UI, so this takes the
shape a query against `projectV2` returns: the project itself, its
`fields`, and its `items` with `fieldValues` and `content` expanded.

GitHub Projects has no fixed notion of a "column". A board view groups
items by whichever single-select field is set as its grouping field, and
almost every project uses one named "Status" for that, but it's a
convention, not a schema guarantee. We look for a single-select field
named "Status" (case-insensitively) and treat its options as columns, in
the order the field defines them; if no such field exists we fall back to
the first single-select field in the project, since that's still the most
likely grouping field. A project with no single-select field at all has no
columns to build, so it comes back with none and every item is dropped.

An item's status isn't a plain field either - it's one entry in the
item's `fieldValues` list, matched back to the status field by name, the
same shape problem the Asana parser has with section membership.

`content` is the issue, pull request, or draft issue the item wraps, and
it can be missing entirely (the underlying issue/PR was deleted after
being added to the project); those items are dropped. Draft issues have
no `closed` or `labels` field, so both default to their empty values.
"""

import json
from pathlib import Path
from typing import Optional

from .model import Board, Card, Column


def _find_status_field(data: dict) -> Optional[dict]:
    fields = [
        f for f in data.get("fields", {}).get("nodes", []) if f.get("options")
    ]
    for f in fields:
        if f.get("name", "").strip().lower() == "status":
            return f
    return fields[0] if fields else None


def _status_option_name(item: dict, status_field_name: str) -> str:
    for value in item.get("fieldValues", {}).get("nodes", []):
        field = value.get("field") or {}
        if field.get("name") == status_field_name and value.get("name"):
            return value["name"]
    return ""


def parse_github_project(data: dict) -> Board:
    status_field = _find_status_field(data)

    columns: list[Column] = []
    columns_by_name: dict[str, Column] = {}
    if status_field is not None:
        for option in status_field.get("options", []):
            column = Column(
                id=option.get("id", option.get("name", "")),
                name=option.get("name", ""),
                position=float(len(columns)),
            )
            columns_by_name[column.name] = column
            columns.append(column)

    if status_field is not None:
        for item in data.get("items", {}).get("nodes", []):
            content = item.get("content")
            if not content or not content.get("id"):
                continue
            column = columns_by_name.get(
                _status_option_name(item, status_field["name"])
            )
            if column is None:
                continue
            card = Card(
                id=content["id"],
                title=content.get("title", ""),
                column=column.name,
                position=float(len(column.cards)),
                description=content.get("body", "") or "",
                labels=[
                    label.get("name", "")
                    for label in content.get("labels", {}).get("nodes", [])
                    if label.get("name")
                ],
                closed=content.get("closed", False),
            )
            column.cards.append(card)

    return Board(id=data.get("id", ""), name=data.get("title", ""), columns=columns)


def load_github_project_file(path: str | Path) -> Board:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return parse_github_project(data)
