import tkinter as tk
from tkinter import messagebox
import random

# Difficulty settings: (min, max)
DIFFICULTY = {
    "Easy": (1, 9),
    "Moderate": (10, 99),
    "Advanced": (1000, 9999)
}

class MathsQuiz:
    def __init__(self, root):
        self.root = root
        self.root.title("Maths Quiz")
        self.score = 0
        self.question_num = 0
        self.difficulty = None
        self.first_attempt = True
        self.current_problem = None
        self.displayMenu()

    def displayMenu(self):
        self.clear()
        tk.Label(self.root, text="DIFFICULTY LEVEL", font=("Arial", 16)).pack(pady=10)
        for level in DIFFICULTY.keys():
            tk.Button(self.root, text=level, width=15, font=("Arial", 12),
                      command=lambda l=level: self.startQuiz(l)).pack(pady=5)

    def startQuiz(self, difficulty):
        self.difficulty = difficulty
        self.score = 0
        self.question_num = 0
        self.nextQuestion()

    def randomInt(self):
        min_val, max_val = DIFFICULTY[self.difficulty]
        return random.randint(min_val, max_val), random.randint(min_val, max_val)

    def decideOperation(self):
        return random.choice(['+', '-'])

    def displayProblem(self):
        self.clear()
        num1, num2 = self.randomInt()
        op = self.decideOperation()
        # For subtraction, ensure non-negative results
        if op == '-' and num1 < num2:
            num1, num2 = num2, num1
        self.current_problem = (num1, num2, op)
        self.first_attempt = True

        tk.Label(self.root, text=f"Question {self.question_num + 1} of 10", font=("Arial", 12)).pack(pady=5)
        tk.Label(self.root, text=f"{num1} {op} {num2} =", font=("Arial", 16)).pack(pady=10)
        self.answer_entry = tk.Entry(self.root, font=("Arial", 14))
        self.answer_entry.pack(pady=5)
        tk.Button(self.root, text="Submit", font=("Arial", 12), command=self.checkAnswer).pack(pady=10)

    def isCorrect(self, user_answer):
        num1, num2, op = self.current_problem
        correct = num1 + num2 if op == '+' else num1 - num2
        return user_answer == correct

    def checkAnswer(self):
        try:
            user_answer = int(self.answer_entry.get())
        except ValueError:
            messagebox.showinfo("Invalid", "Please enter a valid integer.")
            return

        if self.isCorrect(user_answer):
            if self.first_attempt:
                self.score += 10
                messagebox.showinfo("Correct!", "Correct! +10 points")
            else:
                self.score += 5
                messagebox.showinfo("Correct!", "Correct! +5 points")
            self.question_num += 1
            if self.question_num < 10:
                self.nextQuestion()
            else:
                self.displayResults()
        else:
            if self.first_attempt:
                self.first_attempt = False
                messagebox.showinfo("Incorrect", "Incorrect! Try again.")
            else:
                messagebox.showinfo("Incorrect", "Incorrect! Moving to next question.")
                self.question_num += 1
                if self.question_num < 10:
                    self.nextQuestion()
                else:
                    self.displayResults()

    def nextQuestion(self):
        self.displayProblem()

    def displayResults(self):
        self.clear()
        grade = self.getGrade(self.score)
        tk.Label(self.root, text=f"Quiz Complete!", font=("Arial", 16)).pack(pady=10)
        tk.Label(self.root, text=f"Your Score: {self.score} / 100", font=("Arial", 14)).pack(pady=5)
        tk.Label(self.root, text=f"Rank: {grade}", font=("Arial", 14)).pack(pady=5)
        tk.Button(self.root, text="Play Again", font=("Arial", 12), command=self.displayMenu).pack(pady=10)
        tk.Button(self.root, text="Exit", font=("Arial", 12), command=self.root.quit).pack(pady=5)

    def getGrade(self, score):
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 60:
            return "C"
        elif score >= 50:
            return "D"
        else:
            return "F"

    def clear(self):
        for widget in self.root.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MathsQuiz(root)
    root.mainloop()