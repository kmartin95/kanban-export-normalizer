"""Parser for an Asana project dumped via the API (GET a project, its
sections, and its tasks with the `memberships` field expanded).

Asana's board view maps sections to columns, but a task's section
membership isn't a plain field on the task - it lives in the `memberships`
array, since a task can belong to multiple projects and has a separate
section per project it's in. We look up the membership entry whose
`project` matches the project we're parsing to find that task's section.

The API also has no per-task ordering field in the same sense Trello's
`pos` does. The tasks list comes back in whatever order the export walked
it in, so we fall back to that order (per section) the same way the Jira
CSV parser falls back to row order.

Tasks with no matching section membership (e.g. the export was filtered,
or the task sits in the project but outside any section) are dropped,
since there's no column to place them in.
"""

import json
from pathlib import Path

from .model import Board, Card, Column


def _section_gid_for_task(task: dict, project_gid: str) -> str:
    for membership in task.get("memberships", []):
        section = membership.get("section")
        project = membership.get("project")
        if not section:
            continue
        if project is None or project.get("gid") == project_gid:
            return section.get("gid", "")
    return ""


def parse_asana(data: dict) -> Board:
    project_gid = data.get("gid", "")

    columns: list[Column] = []
    columns_by_gid: dict[str, Column] = {}
    for raw_section in data.get("sections", []):
        column = Column(
            id=raw_section["gid"],
            name=raw_section.get("name", ""),
            position=float(len(columns)),
        )
        columns_by_gid[column.id] = column
        columns.append(column)

    for raw_task in data.get("tasks", []):
        section_gid = _section_gid_for_task(raw_task, project_gid)
        column = columns_by_gid.get(section_gid)
        if column is None:
            continue
        card = Card(
            id=raw_task["gid"],
            title=raw_task.get("name", ""),
            column=column.name,
            position=float(len(column.cards)),
            description=raw_task.get("notes", ""),
            labels=[
                tag.get("name", "")
                for tag in raw_task.get("tags", [])
                if tag.get("name")
            ],
            closed=raw_task.get("completed", False),
        )
        column.cards.append(card)

    return Board(id=project_gid, name=data.get("name", ""), columns=columns)


def load_asana_file(path: str | Path) -> Board:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return parse_asana(data)
