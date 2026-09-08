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

Trello, Jira (CSV export), Asana, and GitHub Projects are implemented so
far.

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

Export issues from Jira (Issues > Export > Export CSV (all fields)) and
load the file:

```python
from kanban_export import load_jira_csv_file

board = load_jira_csv_file("my-project.csv")

for column in board.columns:
    print(f"  {column.name}: {len(column.cards)} cards")
```

Jira's CSV export has no board-level id or explicit card ordering, so
`board.id`/`board.name` come from the Project key/name columns, and card
position within a column falls back to the row order in the export.

Asana has no bulk "export as JSON" button in the UI, so this parser takes
the shape you get back from the API: a project (`gid`, `name`), its
`sections`, and its `tasks` with `memberships` expanded so each task can
be matched back to a section:

```python
from kanban_export import parse_asana

board = parse_asana(project_dict)
```

or from a file you've already saved that response to:

```python
from kanban_export import load_asana_file

board = load_asana_file("my-project.json")
```

Like Jira, Asana's API doesn't expose a per-task ordering field, so card
position within a column falls back to the order tasks appear in the
`tasks` list.

GitHub Projects (the v2 kind, at org or user level) also has no export
button — pull it via the GraphQL API's `projectV2` query, with `fields`
and `items` (including `fieldValues` and `content`) expanded, and pass the
resulting project object straight in:

```python
from kanban_export import parse_github_project

board = parse_github_project(project_dict)
```

or from a saved copy of that response:

```python
from kanban_export import load_github_project_file

board = load_github_project_file("my-project.json")
```

Columns come from the project's "Status" single-select field (or its
first single-select field, if none is named "Status") — GitHub Projects
has no dedicated column concept, just whichever field a board view groups
by, and "Status" is the near-universal convention. Card position falls
back to item order, same as Jira and Asana.

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
