# kanban-export-normalizer

Every kanban tool exports its board data in its own shape. Trello's export
nests nothing and makes you join cards back to lists by id. Jira's CSV
export flattens everything into rows with tool-specific column names.
Asana's export has yet another shape. If you want to write a script that
computes cycle time, or migrates cards from one tool to another, or just
counts how many cards are stuck in "In Review", you end up writing that
join-and-normalize logic from scratch for whichever tool you happen to be
using that week.

This library does the normalizing once. Every parser takes a tool's native
export and returns the same three types: `Board`, `Column`, `Card`. Write
your analytics or migration code against that model and it doesn't care
which tool the data came from.

Only Trello is implemented so far. Jira and Asana parsers are planned (see
the roadmap below) — they should be a matter of writing a new module that
produces the same `Board` shape, not changing the model.

## Install

No PyPI package yet. Clone it and install in editable mode:

```
pip install -e .
```

No third-party dependencies — standard library only.

## Usage

Export a board from Trello (Menu > More > Print and Export > Export as
JSON) and load it:

```python
from kanban_export import load_trello_file

board = load_trello_file("my-board.json")

print(board.name)
for column in board.columns:
    print(f"  {column.name}: {len(column.cards)} cards")

# work across the whole board without caring which column a card is in
open_cards = [card for card in board.all_cards() if not card.closed]
print(f"{len(open_cards)} open cards")

review = board.column_by_name("In Review")
if review:
    for card in review.cards:
        print(card.title, card.labels)
```

If you already have the export loaded as a dict (e.g. pulled from the
Trello API instead of a file), use `parse_trello` directly:

```python
from kanban_export import parse_trello

board = parse_trello(exported_dict)
```

## Data model

```python
@dataclass
class Card:
    id: str
    title: str
    column: str          # name of the column the card currently sits in
    position: float       # the tool's own ordering value within the column
    description: str
    labels: list[str]
    closed: bool           # archived/done, depending on the source tool

@dataclass
class Column:
    id: str
    name: str
    position: float
    cards: list[Card]

@dataclass
class Board:
    id: str
    name: str
    columns: list[Column]
```

## License

MIT, see LICENSE.
