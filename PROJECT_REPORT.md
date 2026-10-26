# Schulte Table Game Using Data Structures in Python

## 1. Abstract
The Schulte Table Game is a desktop application designed to practise visual
search and concentration. A randomized grid displays numbers, and the player
must select them in ascending order. The application records completion time,
mistakes, and score. It demonstrates practical uses of lists, stacks, nested
lists, dictionaries, and file-based data persistence.

## 2. Introduction
The project converts the traditional Schulte Table activity into an interactive
Python application. Tkinter provides the graphical interface, while Python data
structures manage the grid and game history.

## 3. Objectives
- Develop a simple, user-friendly desktop game.
- Apply lists to store and randomize grid values.
- Apply a stack to implement Undo using LIFO.
- Store results in dictionaries and save them to JSON.
- Measure completion time and mistakes.

## 4. Software Requirements
- Operating system: Windows, Linux, or macOS with a graphical desktop
- Python 3.9 or later recommended
- Tkinter GUI library
- Visual Studio Code or another Python editor (optional)

## 5. System Design
**Input:** player name, grid size, and number-button clicks.

**Processing:** validate the next expected number, update the stack, timer,
mistake counter, and score.

**Output:** randomized grid, progress, completion time, score, and leaderboard.

**Flow:** Start → Select grid → Generate shuffled list → Display grid → Accept
click → Check expected number → Update game state → Repeat until all numbers
are selected → Save result → Show summary.

## 6. Data Structures
- **List:** `numbers` stores the sequence from 1 to N² and is shuffled.
- **Stack:** `history` stores correct selections. Undo uses `pop()` to reverse
  the latest selection.
- **Dictionary:** each result contains player, grid, time, mistakes, score,
  and completion date.
- **Nested list:** `buttons` represents the rows and columns of GUI buttons.
- **JSON persistence:** completed results are stored in `data/scores.json`.

## 7. Algorithm
1. Read the chosen grid size N.
2. Create a list containing 1 through N².
3. Shuffle the list and display it in an N × N grid.
4. Start the timer on the first click.
5. If the clicked number equals the expected number, push the move onto the
   stack, disable and colour the button, and increment the expected number.
6. Otherwise, increment the mistake counter.
7. When N² is selected correctly, stop the timer, calculate the score, save
   the result, and show the summary.
8. Undo pops the last correct move and enables that cell again.

## 8. Complexity Analysis
Let N be the number of cells (N = grid size squared).
- Creating the list: O(N)
- Shuffling: O(N) expected
- Checking a clicked cell: O(1)
- Stack push/pop: O(1)
- Drawing the grid: O(N)
- Loading and sorting saved leaderboard results: O(R log R), where R is the
  number of saved results

## 9. Testing
| Test case | Input/action | Expected output |
|---|---|---|
| 1 | Start a new game | Randomized grid is displayed |
| 2 | Click the expected number | Cell turns green; target increments |
| 3 | Click a wrong number | Mistake count increases |
| 4 | Press Undo after a correct move | Latest correct move is restored |
| 5 | Complete all numbers | Timer stops and result summary appears |
| 6 | Open Leaderboard | Saved results are displayed |
| 7 | Select another grid size | New grid of selected size appears |

## 10. Limitations
Results are saved locally on the same computer. The timer continues during
Undo, and Undo does not reduce mistakes. The score formula is a simple project
scoring rule rather than a standardized performance measure.

## 11. Conclusion
The Schulte Table Game demonstrates how core data structures can be integrated
into a practical GUI application. Lists manage the randomized grid, a stack
supports Undo, and dictionaries with JSON persistence store performance
records. The project can be extended with profiles, graphs, and additional
game modes.
