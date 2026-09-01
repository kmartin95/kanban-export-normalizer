"""Parser for Jira's CSV issue export (Issues > Export > Export CSV (all fields)).

Jira's CSV export is row-per-issue, and it repeats the column header for
multi-valued fields like Labels instead of putting all values in one
delimited cell. csv.DictReader silently keeps only the last column for a
repeated header, so we walk the header ourselves and collect every column
index sharing a name.

The export also has no explicit board/list structure: there's no list of
statuses or a rank field, just whatever order the query returned rows in
(usually issue key or creation order). We treat each distinct Status value
as a column, in first-seen order, and each column's card order as the row
order within that status. That's enough to count cards per column and read
titles/labels, but it won't reproduce a swimlane's exact drag-and-drop
order, since a CSV export doesn't carry one.

"Closed" is inferred from the Resolution field being set, which is the
usual Jira convention: an issue gets a resolution when it's resolved,
regardless of which status name a project used for its closed state.
"""

import csv
from pathlib import Path
from typing import Iterable

from .model import Board, Card, Column


def _index_columns_by_name(header: list[str]) -> dict[str, list[int]]:
    indices_by_name: dict[str, list[int]] = {}
    for index, name in enumerate(header):
        indices_by_name.setdefault(name, []).append(index)
    return indices_by_name


def _expand_rows(reader: Iterable[list[str]], header: list[str]) -> list[dict[str, list[str]]]:
    indices_by_name = _index_columns_by_name(header)
    rows = []
    for raw_row in reader:
        row: dict[str, list[str]] = {}
        for name, indices in indices_by_name.items():
            row[name] = [
                raw_row[index]
                for index in indices
                if index < len(raw_row) and raw_row[index].strip()
            ]
        rows.append(row)
    return rows


def _first(values: list[str]) -> str:
    return values[0] if values else ""


def parse_jira_csv(text: str) -> Board:
    reader = csv.reader(text.splitlines())
    try:
        header = next(reader)
    except StopIteration:
        return Board(id="", name="", columns=[])

    rows = _expand_rows(reader, header)

    columns: list[Column] = []
    columns_by_name: dict[str, Column] = {}
    project_key = ""
    project_name = ""

    for row in rows:
        status = _first(row.get("Status", []))
        if not status:
            continue

        column = columns_by_name.get(status)
        if column is None:
            column = Column(id=status, name=status, position=float(len(columns)))
            columns_by_name[status] = column
            columns.append(column)

        if not project_key:
            project_key = _first(row.get("Project key", []))
        if not project_name:
            project_name = _first(row.get("Project name", []))

        card_id = _first(row.get("Issue key", [])) or _first(row.get("Issue id", []))
        if not card_id:
            continue

        card = Card(
            id=card_id,
            title=_first(row.get("Summary", [])),
            column=column.name,
            position=float(len(column.cards)),
            description=_first(row.get("Description", [])),
            labels=row.get("Labels", []),
            closed=bool(_first(row.get("Resolution", []))),
        )
        column.cards.append(card)

    return Board(id=project_key, name=project_name or project_key, columns=columns)


def load_jira_csv_file(path: str | Path) -> Board:
    with open(path, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    return parse_jira_csv(text)
