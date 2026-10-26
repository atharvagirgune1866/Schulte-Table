# Data Structures Notes — Schulte Table

## List
`numbers = list(range(1, grid_size * grid_size + 1))` stores the values.
`random.shuffle(numbers)` randomizes their order. Accessing a clicked cell
uses its row and column to calculate an index, so the lookup is O(1).

## Stack
`history` stores each correct move as `(row, column, number)`.
- Push: `history.append(move)`
- Pop: `history.pop()`
The most recently correct move is undone first, which follows LIFO.

## Dictionary
A completed result is represented as a dictionary:
- player
- grid
- time_seconds
- mistakes
- score
- completed_at

## Nested list
`buttons[row][column]` stores the button widgets arranged as a 2D grid.

## Persistence
The leaderboard is stored in `data/scores.json` so results remain available
after the application closes.
