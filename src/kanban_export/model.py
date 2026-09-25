"""Common data model that every board-specific parser normalizes into."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterator, Optional


@dataclass
class Card:
    id: str
    title: str
    column: str
    position: float
    description: str = ""
    labels: list[str] = field(default_factory=list)
    closed: bool = False
    # Not every export carries both of these - a parser leaves whichever
    # one its source format doesn't provide as None.
    created_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None


@dataclass
class Column:
    id: str
    name: str
    position: float
    cards: list[Card] = field(default_factory=list)


@dataclass
class Board:
    id: str
    name: str
    columns: list[Column] = field(default_factory=list)

    def column_by_id(self, column_id: str) -> Optional[Column]:
        for column in self.columns:
            if column.id == column_id:
                return column
        return None

    def column_by_name(self, name: str) -> Optional[Column]:
        for column in self.columns:
            if column.name == name:
                return column
        return None

    def all_cards(self) -> Iterator[Card]:
        for column in self.columns:
            yield from column.cards
