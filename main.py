import tkinter as tk
from tkinter import messagebox, ttk
import random
import time
import json
import os
from datetime import datetime

APP_TITLE = "Schulte Table | Data Structures Project"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
SCORES_FILE = os.path.join(DATA_DIR, "scores.json")


class SchulteTableApp:
    """Schulte Table game demonstrating lists, stacks, and dictionaries."""

    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("760x760")
        self.root.minsize(650, 680)
        self.root.configure(bg="#f3f6fb")

        self.grid_size = tk.IntVar(value=5)
        self.player_name = tk.StringVar(value="Player")
        self.expected = 1
        self.mistakes = 0
        self.numbers = []
        self.history = []  # Stack: (row, col, number)
        self.buttons = []
        self.started = False
        self.completed = False
        self.start_time = None
        self.elapsed = 0.0
        self.timer_job = None

        self._build_ui()
        self.new_game()

    def _build_ui(self):
        header = tk.Frame(self.root, bg="#17324d", padx=18, pady=16)
        header.pack(fill="x")
        tk.Label(
            header, text="SCHULTE TABLE", font=("Times New Roman", 25, "bold"),
            fg="white", bg="#17324d"
        ).pack()
        controls = tk.Frame(self.root, bg="#f3f6fb", padx=16, pady=12)
        controls.pack(fill="x")

        tk.Label(controls, text="Player:", bg="#f3f6fb",
                 font=("Times New Roman", 12, "bold")).grid(row=0, column=0, sticky="w")
        tk.Entry(controls, textvariable=self.player_name, width=16,
                 font=("Times New Roman", 12)).grid(row=0, column=1, padx=(6, 18))

        tk.Label(controls, text="Grid:", bg="#f3f6fb",
                 font=("Times New Roman", 12, "bold")).grid(row=0, column=2, sticky="w")
        size_box = ttk.Combobox(controls, textvariable=self.grid_size,
                                values=(3, 4, 5, 6), width=5, state="readonly")
        size_box.grid(row=0, column=3, padx=6)
        size_box.bind("<<ComboboxSelected>>", lambda _event: self.new_game())

        tk.Button(
            controls, text="New / Restart", command=self.new_game,
            bg="#286090", fg="white", activebackground="#1f4f78",
            font=("Times New Roman", 11, "bold"), relief="flat", padx=12, pady=5
        ).grid(row=0, column=4, padx=(12, 0))

        stats = tk.Frame(self.root, bg="#ffffff", highlightbackground="#d7e0eb",
                         highlightthickness=1, padx=12, pady=10)
        stats.pack(fill="x", padx=16, pady=(0, 8))
        self.target_label = tk.Label(stats, text="Find: 1",
                                     font=("Times New Roman", 15, "bold"),
                                     bg="white", fg="#17324d")
        self.target_label.grid(row=0, column=0, padx=12, sticky="w")
        self.timer_label = tk.Label(stats, text="Time: 0.00 s",
                                    font=("Times New Roman", 15, "bold"),
                                    bg="white", fg="#17324d")
        self.timer_label.grid(row=0, column=1, padx=12)
        self.mistakes_label = tk.Label(stats, text="Mistakes: 0",
                                       font=("Times New Roman", 15, "bold"),
                                       bg="white", fg="#a33a3a")
        self.mistakes_label.grid(row=0, column=2, padx=12)
        stats.grid_columnconfigure((0, 1, 2), weight=1)

        self.status_label = tk.Label(
            self.root, text="",
            font=("Times New Roman", 12), bg="#f3f6fb", fg="#354b60", wraplength=680
        )
        self.status_label.pack(pady=(3, 8))

        self.grid_frame = tk.Frame(self.root, bg="#d7e0eb", padx=6, pady=6)
        self.grid_frame.pack(padx=18, pady=8)

        action_frame = tk.Frame(self.root, bg="#f3f6fb")
        action_frame.pack(pady=8)
        tk.Button(
            action_frame, text="Undo Last Correct Move", command=self.undo_move,
            bg="#f0c36d", fg="#2d2d2d", font=("Times New Roman", 11, "bold"),
            relief="flat", padx=12, pady=7
        ).grid(row=0, column=0, padx=6)
        tk.Button(
            action_frame, text="Leaderboard", command=self.show_leaderboard,
            bg="#3a806d", fg="white", font=("Times New Roman", 11, "bold"),
            relief="flat", padx=12, pady=7
        ).grid(row=0, column=1, padx=6)

    def new_game(self):
        self._cancel_timer()
        self.expected = 1
        self.mistakes = 0
        self.history = []
        self.started = False
        self.completed = False
        self.start_time = None
        self.elapsed = 0.0

        size = int(self.grid_size.get())
        self.numbers = list(range(1, size * size + 1))  # List data structure
        random.shuffle(self.numbers)
        self._draw_grid()

        self.target_label.config(text="Find: 1")
        self.timer_label.config(text="Time: 0.00 s")
        self.mistakes_label.config(text="Mistakes: 0")
        self.status_label.config(text="")

    def _draw_grid(self):
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        self.buttons = []
        size = int(self.grid_size.get())
        cell_width = 7 if size <= 5 else 6
        font_size = 19 if size <= 4 else (16 if size == 5 else 13)

        for r in range(size):
            row_buttons = []
            for c in range(size):
                number = self.numbers[r * size + c]
                btn = tk.Button(
                    self.grid_frame, text=str(number), width=cell_width, height=2,
                    font=("Times New Roman", font_size, "bold"),
                    bg="white", fg="#17324d", activebackground="#dce8f4",
                    relief="raised", bd=2,
                    command=lambda rr=r, cc=c: self.on_number_click(rr, cc)
                )
                btn.grid(row=r, column=c, padx=4, pady=4, sticky="nsew")
                row_buttons.append(btn)
            self.buttons.append(row_buttons)

    def on_number_click(self, row, col):
        if self.completed:
            return
        size = int(self.grid_size.get())
        number = self.numbers[row * size + col]

        if not self.started:
            self.started = True
            self.start_time = time.perf_counter()
            self._tick()

        if number == self.expected:
            self.history.append((row, col, number))  # Stack push
            self.buttons[row][col].config(bg="#8fcea8", fg="#123d2a", state="disabled")
            self.expected += 1
            total = size * size
            if self.expected <= total:
                self.target_label.config(text=f"Find: {self.expected}")
                self.status_label.config(text=f"Correct! Now find {self.expected}.")
            else:
                self._finish_game()
        else:
            self.mistakes += 1
            self.mistakes_label.config(text=f"Mistakes: {self.mistakes}")
            self.status_label.config(text=f"Not quite—look for {self.expected}.", fg="#a33a3a")
            self.root.after(900, lambda: self.status_label.config(fg="#354b60"))

    def _tick(self):
        if self.started and not self.completed:
            self.elapsed = time.perf_counter() - self.start_time
            self.timer_label.config(text=f"Time: {self.elapsed:.2f} s")
            self.timer_job = self.root.after(100, self._tick)

    def _finish_game(self):
        self.completed = True
        self.started = False
        self._cancel_timer()
        self.elapsed = time.perf_counter() - self.start_time
        total = int(self.grid_size.get()) ** 2
        score = max(0, 1000 - int(self.elapsed * 5) - self.mistakes * 20)
        result = {
            "player": self.player_name.get().strip() or "Player",
            "grid": f"{self.grid_size.get()}x{self.grid_size.get()}",
            "time_seconds": round(self.elapsed, 2),
            "mistakes": self.mistakes,
            "score": score,
            "completed_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        self._save_result(result)
        self.target_label.config(text="Complete!")
        self.status_label.config(
            text=f"Well done, {result['player']}! Final score: {score}/1000. Your result has been saved."
        )
        messagebox.showinfo(
            "Game Completed",
            f"Congratulations, {result['player']}!\\n\\n"
            f"Grid: {result['grid']}\\n"
            f"Time: {result['time_seconds']} seconds\\n"
            f"Mistakes: {result['mistakes']}\\n"
            f"Score: {result['score']}/1000"
        )

    def undo_move(self):
        if not self.history or self.completed:
            self.status_label.config(text="There is no correct move to undo.")
            return
        row, col, number = self.history.pop()  # Stack pop (LIFO)
        self.expected = number
        self.buttons[row][col].config(bg="white", fg="#17324d", state="normal")
        self.target_label.config(text=f"Find: {self.expected}")
        self.status_label.config(text=f"Move {number} undone. Find {self.expected}.")
        # The timer and mistake count intentionally continue unchanged.

    def _save_result(self, result):
        os.makedirs(DATA_DIR, exist_ok=True)
        results = self._load_results()
        results.append(result)
        with open(SCORES_FILE, "w", encoding="utf-8") as file:
            json.dump(results, file, indent=2)

    def _load_results(self):
        if not os.path.exists(SCORES_FILE):
            return []
        try:
            with open(SCORES_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def show_leaderboard(self):
        results = sorted(
            self._load_results(),
            key=lambda item: (item.get("time_seconds", float("inf")), item.get("mistakes", 0))
        )
        win = tk.Toplevel(self.root)
        win.title("Schulte Table Leaderboard")
        win.geometry("700x360")
        win.configure(bg="#f3f6fb")
        tk.Label(win, text="LEADERBOARD", font=("Times New Roman", 18, "bold"),
                 bg="#f3f6fb", fg="#17324d").pack(pady=12)

        columns = ("rank", "player", "grid", "time", "mistakes", "score", "date")
        tree = ttk.Treeview(win, columns=columns, show="headings", height=10)
        headings = {
            "rank": "Rank", "player": "Player", "grid": "Grid",
            "time": "Time (s)", "mistakes": "Mistakes",
            "score": "Score", "date": "Completed"
        }
        widths = {"rank": 48, "player": 115, "grid": 65, "time": 85,
                  "mistakes": 75, "score": 70, "date": 130}
        for col in columns:
            tree.heading(col, text=headings[col])
            tree.column(col, width=widths[col], anchor="center")
        tree.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        for rank, item in enumerate(results[:50], start=1):
            tree.insert("", "end", values=(
                rank, item.get("player", "Player"), item.get("grid", "-"),
                item.get("time_seconds", "-"), item.get("mistakes", "-"),
                item.get("score", "-"), item.get("completed_at", "-")
            ))
        if not results:
            tk.Label(win, text="No saved results yet. Finish a game to add a score.",
                     bg="#f3f6fb", font=("Times New Roman", 11)).pack(pady=4)

    def _cancel_timer(self):
        if self.timer_job is not None:
            try:
                self.root.after_cancel(self.timer_job)
            except tk.TclError:
                pass
            self.timer_job = None


if __name__ == "__main__":
    root = tk.Tk()
    app = SchulteTableApp(root)
    root.mainloop()
