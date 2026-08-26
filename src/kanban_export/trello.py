"""Parser for Trello's board export format (Menu > More > Print and Export > JSON).

Trello's export is a flat structure: a board has a `lists` array and a
separate `cards` array where each card points back at its list via `idList`.
We rebuild the nesting here and drop archived (`closed`) lists, since an
archived list's cards usually aren't meant to count toward the live board.
"""

import json
from pathlib import Path

from .model import Board, Card, Column


def parse_trello(data: dict) -> Board:
    columns: list[Column] = []
    columns_by_id: dict[str, Column] = {}

    for raw_list in data.get("lists", []):
        if raw_list.get("closed"):
            continue
        column = Column(
            id=raw_list["id"],
            name=raw_list.get("name", ""),
            position=raw_list.get("pos", 0.0),
        )
        columns_by_id[column.id] = column
        columns.append(column)

    for raw_card in data.get("cards", []):
        column = columns_by_id.get(raw_card.get("idList"))
        if column is None:
            continue
        card = Card(
            id=raw_card["id"],
            title=raw_card.get("name", ""),
            column=column.name,
            position=raw_card.get("pos", 0.0),
            description=raw_card.get("desc", ""),
            labels=[
                label.get("name", "")
                for label in raw_card.get("labels", [])
                if label.get("name")
            ],
            closed=raw_card.get("closed", False),
        )
        column.cards.append(card)

    for column in columns:
        column.cards.sort(key=lambda c: c.position)
    columns.sort(key=lambda c: c.position)

    return Board(id=data.get("id", ""), name=data.get("name", ""), columns=columns)


def load_trello_file(path: str | Path) -> Board:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return parse_trello(data)
