SCHULTE TABLE GAME — DATA STRUCTURES MINI PROJECT
===================================================

OVERVIEW
--------
A desktop Schulte Table game built with Python and Tkinter. Players click the
numbers in ascending order. It includes a timer, mistake counter, score, undo,
grid-size selection, and a saved leaderboard.

DATA STRUCTURES DEMONSTRATED
----------------------------
1. List: stores and shuffles the numbers displayed in the grid.
2. Stack: stores correct moves; Undo removes the most recent move (LIFO).
3. Dictionary: represents one completed game result.
4. Nested list: stores the GUI buttons as rows and columns.
5. JSON file: persists completed scores between sessions.

REQUIREMENTS
------------
- Python 3.9 or later recommended
- Tkinter (included with many Python installations)
- No pip packages are required

HOW TO RUN
----------
1. Extract the ZIP folder.
2. Open the extracted SchulteTable_DS_Project folder in VS Code.
3. Open Terminal > New Terminal.
4. Run:
       python main.py
   On Windows, you can also try:
       py main.py

PROJECT FILES
-------------
main.py            Main game application
data/scores.json   Saved leaderboard results (created automatically)
docs/PROJECT_REPORT.md  Short project report
docs/DS_NOTES.md   Data structures and complexity notes

GAME INSTRUCTIONS
-----------------
- Enter a player name.
- Choose a 3x3, 4x4, 5x5, or 6x6 grid.
- Click numbers in ascending order, starting from 1.
- Correct selections turn green.
- Incorrect selections increase the mistake count.
- Use Undo Last Correct Move to reverse the latest correct selection.
- Select Leaderboard to view saved game results.
- New / Restart starts a fresh randomized game.

SCORING
-------
Score = max(0, 1000 - int(time_seconds * 5) - mistakes * 20)

NOTES
-----
- The timer starts on the first click.
- Undo does not reduce the mistake count or pause the timer.
- Saved results are stored locally in data/scores.json.
- This is an educational project, not a clinical attention assessment.
