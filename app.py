
from datetime import datetime
from flask import Flask, render_template, request, redirect
import sqlite3

conn = sqlite3.connect("expenses.db", check_same_thread=False)
cursor = conn.cursor()

app = Flask(__name__)


@app.route("/")
def home():
    cursor.execute("SELECT * FROM expenses")
    expenses = cursor.fetchall()

    # Calculate total spending
    total_spent = sum(float(expense[1]) for expense in expenses)

    # Calculate number of transactions
    transaction_count = len(expenses)

    # Calculate category-wise spending
    category_totals = {}

    for expense in expenses:
        category = expense[2]
        amount = float(expense[1])

        if category in category_totals:
            category_totals[category] += amount
        else:
            category_totals[category] = amount

    category_breakdown = []

    for category, amount in category_totals.items():
        percentage = (amount / total_spent * 100) if total_spent else 0

        category_breakdown.append({
            "name": category,
            "amount": amount,
            "percentage": percentage
        })

    category_breakdown.sort(
        key=lambda item: item["amount"],
        reverse=True
    )

    # Calculate spending in the current month
    current_month = datetime.now().month
    current_year = datetime.now().year

    monthly_spent = 0

    for expense in expenses:
        expense_date = expense[3]

        try:
            parsed_date = datetime.strptime(
                expense_date, "%Y-%m-%d"
            )
        except ValueError:
            try:
                parsed_date = datetime.strptime(
                    expense_date, "%d/%m/%Y"
                )
            except ValueError:
                continue

        if (parsed_date.month == current_month and
                parsed_date.year == current_year):
            monthly_spent += float(expense[1])

    return render_template(
        "index.html",
        expenses=expenses,
        total_spent=total_spent,
        monthly_spent=monthly_spent,
        transaction_count=transaction_count,
        category_breakdown=category_breakdown
    )


@app.route("/add", methods=["POST"])
def add_expense():
    try:
        amount = float(request.form["amount"])
        category = request.form["category"].strip()
        date = request.form["date"]
        description = request.form["description"].strip()

        if amount <= 0:
            return "Amount must be greater than zero!", 400

        if not category or not date:
            return "Category and date are required!", 400

        datetime.strptime(date, "%Y-%m-%d")

    except ValueError:
        return "Please enter a valid amount and date!", 400

    cursor.execute("""
        INSERT INTO expenses(amount, category, date, description)
        VALUES(?, ?, ?, ?)
    """, (amount, category, date, description))

    conn.commit()
    return redirect("/")


@app.route("/edit/<int:expense_id>", methods=["GET", "POST"])
def edit_expense(expense_id):
    if request.method == "POST":
        try:
            amount = float(request.form["amount"])
            category = request.form["category"].strip()
            date = request.form["date"]
            description = request.form["description"].strip()

            if amount <= 0:
                return "Amount must be greater than zero!", 400

            if not category or not date:
                return "Category and date are required!", 400

            datetime.strptime(date, "%Y-%m-%d")

        except ValueError:
            return "Please enter a valid amount and date!", 400

        cursor.execute("""
            UPDATE expenses
            SET amount = ?, category = ?, date = ?, description = ?
            WHERE id = ?
        """, (amount, category, date, description, expense_id))

        conn.commit()
        return redirect("/")

    cursor.execute(
        "SELECT * FROM expenses WHERE id = ?",
        (expense_id,)
    )

    expense = cursor.fetchone()

    if expense is None:
        return "Expense not found!", 404

    return render_template("edit.html", expense=expense)


@app.route("/delete/<int:expense_id>", methods=["POST"])
def delete_expense(expense_id):
    cursor.execute(
        "DELETE FROM expenses WHERE id = ?",
        (expense_id,)
    )

    conn.commit()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
