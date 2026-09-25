"""Lead-time helpers built on the created_at/closed_at fields on Card.

Lead time here is the full time a card was open: from creation to
completion. It is deliberately not called "cycle time" - cycle time
usually means work-start to completion, which requires knowing when a
card entered whichever column counts as "in progress". None of the four
formats this library parses (Trello's board export, Jira's CSV export,
Asana's API response, GitHub's GraphQL response) include a history of
column transitions, only a card's current column, so that timestamp
doesn't exist to read. Lead time is the closest metric these exports can
actually support.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Iterable, Optional

from .model import Board, Card


def lead_time(card: Card) -> Optional[timedelta]:
    """Time from creation to completion, or None if the card isn't closed
    or is missing one of the two timestamps."""
    if not card.closed or card.created_at is None or card.closed_at is None:
        return None
    return card.closed_at - card.created_at


def average_lead_time(cards: Iterable[Card]) -> Optional[timedelta]:
    lead_times = [lt for lt in (lead_time(card) for card in cards) if lt is not None]
    if not lead_times:
        return None
    return sum(lead_times, timedelta()) / len(lead_times)


def average_lead_time_by_column(board: Board) -> dict[str, timedelta]:
    """Average lead time of closed cards, grouped by whichever column each
    one currently sits in. Columns with no closed cards carrying both
    timestamps are left out rather than reported as a misleading zero."""
    by_column: dict[str, list[timedelta]] = defaultdict(list)
    for card in board.all_cards():
        lt = lead_time(card)
        if lt is not None:
            by_column[card.column].append(lt)
    return {
        column: sum(times, timedelta()) / len(times)
        for column, times in by_column.items()
    }


def card_age(card: Card, as_of: datetime) -> Optional[timedelta]:
    """How long an open card has existed as of `as_of`. Useful for spotting
    stale cards given that true cycle time isn't available. `as_of` must
    have the same timezone-awareness as card.created_at (aware for every
    source except Jira rows whose date format carried no offset)."""
    if card.closed or card.created_at is None:
        return None
    return as_of - card.created_at
